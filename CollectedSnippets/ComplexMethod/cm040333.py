def dot_product_attention(
    query,
    key,
    value,
    bias=None,
    mask=None,
    scale=None,
    is_causal=False,
    flash_attention=None,
    attn_logits_soft_cap=None,
):
    query = convert_to_tensor(query)
    key = convert_to_tensor(key)
    value = convert_to_tensor(value)
    if len(query.shape) != 4 or len(key.shape) != 4 or len(value.shape) != 4:
        raise ValueError(
            "`dot_product_attention` only supports 4D inputs. "
            f"Received: query.shape={query.shape}, key.shape={key.shape}, "
            f"value.shape={value.shape}."
        )
    if bias is not None and mask is not None:
        raise ValueError(
            "Only one of `bias` and `mask` can be provided. Received both."
        )
    compute_dtype = backend.result_type(query.dtype, key.dtype, value.dtype)
    query = cast(query, compute_dtype)
    key = cast(key, compute_dtype)
    value = cast(value, compute_dtype)

    mask = mask if mask is None else convert_to_tensor(mask, dtype="bool")
    if mask is not None:
        # Explicit set `is_causal` to `False` when `mask` is not `None`.
        is_causal = False
        mask = torch.where(mask, 0.0, _get_large_negative(query.dtype))
    if bias is not None:
        bias = convert_to_tensor(bias, dtype=compute_dtype)
        mask = bias  # Use `bias` as `mask` for scaled_dot_product_attention.

    axis0, axis1 = 1, 2
    query = torch.transpose(query, axis0, axis1)
    key = torch.transpose(key, axis0, axis1)
    value = torch.transpose(value, axis0, axis1)

    if flash_attention is None:
        flash_attention = _can_use_flash_attention(
            query, key, value, mask, is_causal
        )
    elif flash_attention is True:
        # Use `raise_error=True` to provide more details if the inputs failed to
        # use flash attention
        _can_use_flash_attention(
            query, key, value, mask, is_causal, raise_error=True
        )
    if flash_attention:
        with torch.nn.attention.sdpa_kernel(
            backends=[torch.nn.attention.SDPBackend.FLASH_ATTENTION],
        ):
            attention_output = torch.nn.functional.scaled_dot_product_attention(
                query,
                key,
                value,
                attn_mask=mask,
                is_causal=is_causal,
                scale=scale,
            )
    else:
        if mask is not None:
            mask = mask.contiguous()
        attention_output = torch.nn.functional.scaled_dot_product_attention(
            query.contiguous(),
            key.contiguous(),
            value.contiguous(),
            attn_mask=mask,
            is_causal=is_causal,
            scale=scale,
        )
    return torch.transpose(attention_output, axis1, axis0)