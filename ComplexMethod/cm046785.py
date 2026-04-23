def get_visible_gpu_count() -> int:
    """
    Return the number of GPUs visible to this process.

    Respects ``CUDA_VISIBLE_DEVICES`` -- if set, only those GPUs count.
    Falls back to physical count if the env var is unset or torch is
    unavailable.  Result is cached after the first call.
    """
    global _visible_gpu_count
    if _visible_gpu_count is not None:
        return _visible_gpu_count

    # Use _get_parent_visible_gpu_spec() which already handles
    # HIP_VISIBLE_DEVICES / ROCR_VISIBLE_DEVICES on ROCm.
    visible_spec = _get_parent_visible_gpu_spec()
    if visible_spec["raw"] is not None:
        raw = visible_spec["raw"].strip()
        if raw == "" or raw == "-1":
            _visible_gpu_count = 0
        elif visible_spec["numeric_ids"] is not None:
            _visible_gpu_count = len(visible_spec["numeric_ids"])
        else:
            _visible_gpu_count = len([x for x in raw.split(",") if x.strip()])
        return _visible_gpu_count

    # No visibility env var set -- try torch, fall back to physical count
    try:
        import torch

        if get_device() == DeviceType.XPU and hasattr(torch, "xpu"):
            _visible_gpu_count = torch.xpu.device_count()
        else:
            _visible_gpu_count = torch.cuda.device_count()
    except Exception:
        _visible_gpu_count = get_physical_gpu_count()

    return _visible_gpu_count