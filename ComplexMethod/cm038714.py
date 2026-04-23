def _resolve_auto_dtype(
    model_type: str,
    config_dtype: torch.dtype,
    *,
    is_pooling_model: bool,
):
    supported_dtypes = [
        dtype
        for dtype in current_platform.supported_dtypes
        if _is_valid_dtype(model_type, dtype)
    ]

    if is_pooling_model and torch.float16 in supported_dtypes:
        preferred_dtype = torch.float16
    else:
        preferred_dtype = supported_dtypes[0]

    # Downcast for float32 models
    if config_dtype == torch.float32:
        config_dtype = preferred_dtype

    if config_dtype in supported_dtypes:
        return config_dtype

    # Ensure device compatibility
    device_name = current_platform.get_device_name()
    device_capability = current_platform.get_device_capability()

    if device_capability is None:
        device_str = f"{device_name!r}"
    else:
        version_str = device_capability.as_version_str()
        device_str = f"{device_name!r} (with compute capability {version_str})"

    logger.warning(
        "Your device %s doesn't support %s. Falling back to %s for compatibility.",
        device_str,
        config_dtype,
        preferred_dtype,
    )

    return preferred_dtype