def _validate_sdpa_input(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attn_mask: torch.Tensor | None = None,
    dropout_p=0.0,
    is_causal=False,
    scale=None,
    allow_lowp_kv=False,
) -> None:
    if not allow_lowp_kv:
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
    if query.dim() < 2 or key.dim() < 2 or value.dim() < 2:
        raise ValueError(
            f"Expected query, key, and value to all be  at least 2 dimensional, but got query.dim: "
            f"{query.dim()}, key.dim: {key.dim()} and value.dim: {value.dim()} instead."
        )