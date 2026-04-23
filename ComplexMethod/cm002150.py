def create_causal_mask_mapping(
    config: PreTrainedConfig,
    inputs_embeds: torch.Tensor,
    attention_mask: torch.Tensor | None,
    past_key_values: Cache | None,
    position_ids: torch.Tensor | None,
    token_type_ids: torch.Tensor | None = None,
    pixel_values: torch.FloatTensor | None = None,
    is_training: bool | None = False,
    is_first_iteration: bool | None = None,
    **kwargs,
) -> dict:
    """
    Overwrites the base `create_masks_for_generate` with `token_type_ids` masking to create the causal mask mapping
    for all kinds of forward passes. NewTaskModel uses a bidirectional mask on the prompt tokens.

    Uses `pixel_values` as an optional input to disambiguate edge cases.
    """
    if is_training and token_type_ids is None:
        raise ValueError("`token_type_ids` is required as a model input when training")

    mask_kwargs = {
        "config": config.get_text_config(),
        "inputs_embeds": inputs_embeds,
        "attention_mask": attention_mask,
        "past_key_values": past_key_values,
        "position_ids": position_ids,
    }
    # Infer if prefill or decoding stage, if the flag isn't passed. This happens only when the mask is constructed
    # from `forward` call. If users run a `forward` call, we have no option to infer `is_first_iteration` because users may be
    # running generation with custom loop. Thus we need to infer it in a `non-perfect` way
    # NOTE: Determining prefill in that case requires checking data values, which is not compile-compatible.
    is_first_iteration = (
        is_first_iteration
        if is_first_iteration
        else (past_key_values is None or not past_key_values.is_initialized or pixel_values is not None)
    )

    if is_first_iteration or not kwargs.get("use_cache", True):
        if token_type_ids is not None:
            # The logic bellow was originally written for Gemma3, where `token_type_ids` is reversed. Let's reverse
            # it to then use exactly the same logic.
            token_type_ids = 1 - token_type_ids
        else:
            logger.warning_once(
                "It is a prefill stage but The `token_type_ids` is not provided. We recommend "
                "passing `token_type_ids` to the model to prevent bad attention masking."
            )
            # NOTE: this branch can't be reached when training because `token_type_ids` is required as a model input.
            token_type_ids = torch.ones_like(inputs_embeds)[:, :, 0]

    # Logic originally copied from Gemma3. It holds up for NewTaskModel as well because NewTaskModel assumes up to one image
    # per prompt AND we reverse `token_type_ids` above. Gemma3 uses a bidirectional mask for images, tagged through
    # `token_type_ids` 1s.
    if token_type_ids is not None and is_first_iteration:
        # We need to pass an additional mask function to account for token type ids, and it needs to be an `or` (to
        # undo the causal masking)

        # First find where a new image block starts: 1 if image and previous not image
        # The images cannot attend to future images, but can attend to all prev images and to itself bidirectionally
        is_image = (token_type_ids == 1).to(inputs_embeds.device)
        is_previous_image = nn.functional.pad(is_image, (1, 0), value=0)[:, :-1]
        new_image_start = is_image & ~is_previous_image
        group_ids = torch.cumsum(new_image_start.int(), dim=1) - 1
        group_ids = torch.where(is_image, group_ids, torch.full_like(token_type_ids, -1))
        mask_kwargs["or_mask_function"] = token_type_ids_mask_function(group_ids)

    return create_masks_for_generate(**mask_kwargs)