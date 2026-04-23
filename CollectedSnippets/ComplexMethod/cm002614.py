def _flash_attention_forward(
    query_states: torch.Tensor,
    key_states: torch.Tensor,
    value_states: torch.Tensor,
    attention_mask: torch.Tensor | None,
    query_length: int,
    is_causal: bool,
    dropout: float = 0.0,
    position_ids: torch.Tensor | None = None,
    softmax_scale: float | None = None,
    sliding_window: int | None = None,
    use_top_left_mask: bool = False,
    softcap: float | None = None,
    deterministic: bool | None = None,
    cu_seq_lens_q: torch.LongTensor | None = None,
    cu_seq_lens_k: torch.LongTensor | None = None,
    max_length_q: int | None = None,
    max_length_k: int | None = None,
    target_dtype: torch.dtype | None = None,
    attn_implementation: str | None = None,
    **kwargs,
):
    """
    Calls the forward method of Flash Attention - if the input hidden states contain at least one padding token
    first unpad the input, then computes the attention scores and pad the final attention scores.

    (Optional) kwargs are described further in `_process_flash_attention_kwargs` and `FlashAttentionKwargs`.

    Args:
        query_states (`torch.Tensor`):
            Input query states to be passed to Flash Attention API
        key_states (`torch.Tensor`):
            Input key states to be passed to Flash Attention API
        value_states (`torch.Tensor`):
            Input value states to be passed to Flash Attention API
        attention_mask (`torch.Tensor`, *optional*):
            The padding mask - corresponds to a tensor of size `(batch_size, seq_len)` where 0 stands for the
            position of padding tokens and 1 for the position of non-padding tokens.
        attn_implementation (`str`, *optional*):
            The attention implementation to use. If None, will default to the one based on the environment.
    """
    (flash_fn, flash_varlen_fn, _, pad_fn, unpad_fn), process_flash_kwargs_fn = lazy_import_flash_attention(
        attn_implementation
    )

    # PEFT possibly silently casts tensors to fp32, this potentially reconverts to correct dtype or is a no op
    query_states, key_states, value_states = fa_peft_integration_check(
        query_states, key_states, value_states, target_dtype
    )

    # Extract the flash attention kwargs that have been requested (and are supported by the implementation)
    flash_kwargs = partial(
        process_flash_kwargs_fn,
        query_length=query_length,
        key_length=key_states.size(1),
        is_causal=is_causal,
        dropout=dropout,
        softmax_scale=softmax_scale,
        sliding_window=sliding_window,
        use_top_left_mask=use_top_left_mask,
        softcap=softcap,
        deterministic=deterministic,
        **kwargs,
    )

    # We will use `flash_varlen_fn` to prevent cross-example attention and also allow padding free approach under two cases:
    # Case 1. If position ids is provided and the position ids indicate packed sequences, see `_is_packed_sequence`.
    # Case 2. Some models pass directly pre-computed `cu_seqlens` so we don't need to infer it from position ids. It is safe to
    # use `flash_varlen_fn` knowing we already have all necessary the kwargs.
    #
    # NOTE: it is user's responsibility to take care of flattening `position_ids` if that's needed by the model.
    # See #39121 for more information.
    is_fa_with_position_ids = _is_packed_sequence(position_ids, batch_size=query_states.size(0))
    is_fa_with_varlen_kwargs = all(
        kwarg is not None for kwarg in (cu_seq_lens_q, cu_seq_lens_k, max_length_q, max_length_k)
    )

    # Contains at least one padding token in the sequence
    if attention_mask is not None:
        q, k, v, indices_q, (cu_seq_lens_q, cu_seq_lens_k), (max_length_q, max_length_k) = _upad_input(
            query_states, key_states, value_states, attention_mask, query_length, unpad_fn
        )

        # TODO for now this is required to work with
        # https://huggingface.co/kernels-community/metal-flash-sdpa/blob/main/torch-ext/metal_flash_sdpa/__init__.py
        if "mps" in str(q.device):
            cu_seq_lens_k = cu_seq_lens_k.clone()

        out_unpad = flash_varlen_fn(
            q,
            k,
            v,
            cu_seqlens_q=cu_seq_lens_q,
            cu_seqlens_k=cu_seq_lens_k,
            **flash_kwargs(max_seqlen_q=max_length_q, max_seqlen_k=max_length_k),
        )
        if isinstance(out_unpad, tuple):
            out_unpad = out_unpad[0]

        out = pad_fn(out_unpad, indices_q, query_states.size(0), query_length)

    # Padding free, i.e. sequences flattened into one total sequence
    elif is_fa_with_varlen_kwargs or is_fa_with_position_ids:
        if cu_seq_lens_q is None or cu_seq_lens_k is None:
            q, k, v, (cu_seq_lens_q, cu_seq_lens_k), (max_length_q, max_length_k) = _prepare_from_posids(
                query_states, key_states, value_states, position_ids
            )
        else:
            q = query_states.reshape(-1, query_states.size(-2), query_states.size(-1))
            k = key_states.reshape(-1, key_states.size(-2), key_states.size(-1))
            v = value_states.reshape(-1, value_states.size(-2), value_states.size(-1))

        # TODO for now this is required to work with
        # https://huggingface.co/kernels-community/metal-flash-sdpa/blob/main/torch-ext/metal_flash_sdpa/__init__.py
        if "mps" in str(q.device):
            cu_seq_lens_k = cu_seq_lens_k.clone()

        out = flash_varlen_fn(
            q,
            k,
            v,
            cu_seqlens_q=cu_seq_lens_q,
            cu_seqlens_k=cu_seq_lens_k,
            **flash_kwargs(max_seqlen_q=max_length_q, max_seqlen_k=max_length_k),
        )
        if isinstance(out, tuple):
            out = out[0]

        out = out.view(query_states.size(0), -1, out.size(-2), out.size(-1))

    # No padding
    else:
        out = flash_fn(query_states, key_states, value_states, **flash_kwargs())
        if isinstance(out, tuple):
            out = out[0]

    return out