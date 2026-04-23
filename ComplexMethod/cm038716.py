def _get_head_dtype(
    config: PretrainedConfig, dtype: torch.dtype, runner_type: str
) -> torch.dtype:
    head_dtype: str | torch.dtype | None = getattr(config, "head_dtype", None)

    if head_dtype == "model":
        return dtype
    elif isinstance(head_dtype, str):
        head_dtype = head_dtype.lower()
        if head_dtype not in _STR_DTYPE_TO_TORCH_DTYPE:
            raise ValueError(f"Unknown dtype: {head_dtype!r}")
        return _STR_DTYPE_TO_TORCH_DTYPE[head_dtype]
    elif isinstance(head_dtype, torch.dtype):
        return head_dtype
    elif head_dtype is None:
        if torch.float32 not in current_platform.supported_dtypes:
            return dtype
        if runner_type == "pooling":
            return torch.float32
        return dtype
    else:
        raise ValueError(f"Unknown dtype: {head_dtype}")