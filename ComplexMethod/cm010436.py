def _validate_sdpa_input(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attn_mask: torch.Tensor | None = None,
    dropout_p=0.0,
    is_causal=False,
    scale=None,
) -> None:
    if (
        not isinstance(query, NestedTensor)
        or not isinstance(key, NestedTensor)
        or not isinstance(value, NestedTensor)
    ):
        raise ValueError(
            f"Expected query, key, and value to be nested tensors, "
            f"but got query.is_nested: {query.is_nested}, key.is_nested: {key.is_nested}, "
            f"and value.is_nested: {value.is_nested} instead."
        )
    if query.dtype != key.dtype or query.dtype != value.dtype:
        raise ValueError(
            f"Expected query, key, and value to have the same dtype, "
            f"but got query.dtype: {query.dtype}, key.dtype: {key.dtype}, "
            f"and value.dtype: {value.dtype} instead."
        )
    if query.device != key.device or query.device != value.device:
        raise ValueError(
            f"Expected query, key, and value to have the same device type, "
            f"but got query.device: {query.device}, key.device: {key.device}, "
            f"and value.device: {value.device} instead."
        )
    if query.dim() < 3 or key.dim() < 3 or value.dim() < 3:
        raise ValueError(
            f"Expected query, key, and value to all be  at least 3 dimensional, but got query.dim: "
            f"{query.dim()}, key.dim: {key.dim()} and value.dim: {value.dim()} instead."
        )
    if query._ragged_idx != key._ragged_idx or query._ragged_idx != value._ragged_idx:
        raise ValueError(
            f"Expected query, key, and value to all be ragged on the same dimension, but got ragged "
            f"dims {query._ragged_idx}, {key._ragged_idx}, and {value._ragged_idx}, respectively."
        )
    if attn_mask is not None:
        # TODO: Figure out whether masks are actually supported for this layout or not
        raise ValueError("Masks are not yet supported!")
        if attn_mask.dtype != torch.bool and attn_mask.dtype != query.dtype:
            raise ValueError(
                f"Expected attn_mask dtype to be bool or to match query dtype, but got attn_mask.dtype: "
                f"{attn_mask.dtype}, and query.dtype: {query.dtype} instead."
            )