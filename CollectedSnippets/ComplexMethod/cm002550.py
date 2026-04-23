def create_chunked_causal_mask(
    config: PreTrainedConfig,
    inputs_embeds: torch.Tensor,
    attention_mask: torch.Tensor | None,
    cache_position: torch.Tensor | None = None,  # not used anymore but kept for BC
    *,
    past_key_values: Cache | None,
    position_ids: torch.Tensor | None = None,
    or_mask_function: Callable | None = None,
    and_mask_function: Callable | None = None,
) -> torch.Tensor | BlockMask | None:
    """
    Create a chunked attention causal mask based on the attention implementation used (stored in the config). This type
    of attention pattern was mostly democratized by Llama4. If `past_key_values` has an hybrid cache structure, this
    function will return the mask corresponding to one of the "chunked_attention" layers (to align to what is needed in the
    `modeling_xxx.py` files).

    Args:
        config (`PreTrainedConfig`):
            The model config.
        inputs_embeds (`torch.Tensor`):
            The input embeddings of shape (batch_size, query_length, hidden_dim). This is used only to infer the
            batch size, query length and dtype.
        attention_mask (`torch.Tensor`, optional):
            The 2D attention mask corresponding to padded tokens of shape (batch_size, number_of_seen_tokens+q_length).
            It can also be an already prepared 4D mask, in which case it is returned as-is.
        cache_position (`torch.Tensor`):
            Deprecated and unused.
        past_key_values (`Cache`, optional):
            The past key values, if we use a cache.
        position_ids (`torch.Tensor`, optional)
            A 2D tensor of shape (batch_size, query_length) indicating the positions of each token in the sequences.
        or_mask_function (`Callable`, optional):
            An optional mask function to combine with the chunked causal mask function (by doing the union of both). This is
            useful to easily overlay another mask on top of the chunked causal one, for example for image tokens handling.
        and_mask_function (`Callable`, optional):
            An optional mask function to combine with the chunked causal mask function (by doing the intersection of both). This is
            useful to easily overlay another mask on top of the chunked causal one, for example for image tokens handling.
    """
    # If we have an hybrid cache structure, here we want to create the mask for the sliding layers
    if hasattr(past_key_values, "is_sliding") and True in past_key_values.is_sliding:
        layer_idx = past_key_values.is_sliding.index(True)
    else:
        layer_idx = 0

    early_exit, attention_mask, packed_sequence_mask, q_length, kv_length, q_offset, kv_offset = (
        _preprocess_mask_arguments(config, inputs_embeds, attention_mask, past_key_values, position_ids, layer_idx)
    )
    if early_exit:
        return attention_mask

    chunk_size = getattr(config, "attention_chunk_size", None)
    if chunk_size is None:
        raise ValueError("Could not find an `attention_chunk_size` argument in the config, or it is not set")

    # Raise if using chunked attention on context too large with FA
    if is_flash_attention_requested(config) and kv_length + kv_offset > chunk_size:
        raise ValueError(
            "Flash attention cannot handle chunked attention, and the key-value length is larger than the chunk size so the "
            "chunked pattern cannot be respected. You should use another `attn_implementation` when instantiating the model"
        )

    batch_size, dtype, device = inputs_embeds.shape[0], inputs_embeds.dtype, inputs_embeds.device
    # For chunked attention and batched inputs, we need to take the number of left padding tokens into account
    # to start the chunk from the actual start of the sequence for the padded sequence
    if attention_mask is not None:
        # Only count the left padding tokens, not all of them
        left_padding_tokens = (attention_mask.cumsum(dim=-1) == torch.zeros_like(attention_mask)).sum(dim=-1)
    else:
        left_padding_tokens = torch.zeros(batch_size, device=device, dtype=int)
    mask_factory_function = chunked_causal_mask_function(chunk_size, left_padding_tokens)
    mask_interface = ALL_MASK_ATTENTION_FUNCTIONS[config._attn_implementation]

    # Defaulting to using non-vmap based mask creations except when detecting
    # users passing custom mask functions (as we cannot guarantee that they
    # are properly index-based as required by our implementation).
    use_vmap = False
    # Do not allow skip if we are compiling (this is to match BC)
    # TODO: cyril -> probably revisit and remove this, but a lot of tests rely on it
    allow_is_causal_skip = not getattr(past_key_values, "is_compileable", False)

    # Allow slight deviations from causal mask
    # Note that it is very important to apply this before any other deviations of the mask (such as packed sequence mask,
    # padding mask, etc) as the resulting mask may otherwise not be correct!
    if or_mask_function is not None:
        if not _is_torch_greater_or_equal_than_2_6:
            raise ValueError("Using `or_mask_function` or `and_mask_function` arguments require torch>=2.6")
        mask_factory_function = or_masks(mask_factory_function, or_mask_function)
        allow_is_causal_skip = False
        use_vmap = True
    if and_mask_function is not None:
        if not _is_torch_greater_or_equal_than_2_6:
            raise ValueError("Using `or_mask_function` or `and_mask_function` arguments require torch>=2.6")
        mask_factory_function = and_masks(mask_factory_function, and_mask_function)
        allow_is_causal_skip = False
        use_vmap = True

    # If we detected packing format
    if packed_sequence_mask is not None:
        mask_factory_function = and_masks(mask_factory_function, packed_sequence_mask_function(packed_sequence_mask))
        allow_is_causal_skip = False

    # We now create the mask
    causal_mask = mask_interface(
        batch_size=batch_size,
        q_length=q_length,
        kv_length=kv_length,
        q_offset=q_offset,
        kv_offset=kv_offset,
        mask_function=mask_factory_function,
        attention_mask=attention_mask,
        allow_is_causal_skip=allow_is_causal_skip,  # additional kwarg for sdpa
        local_size=chunk_size,  # Additional kwarg for sdpa
        dtype=dtype,  # Additional kwarg for eager
        config=config,  # Pass the config as well, in case someone wants to easily have their own mask_interface
        use_vmap=use_vmap,  # Short-circuit to non-vmap expansions for the mask
        device=device,
    )
    return causal_mask