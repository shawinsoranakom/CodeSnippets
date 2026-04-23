def get_physical_gpu_count() -> int:
    """
    Return the number of physical GPUs on the machine.

    Uses ``nvidia-smi -L`` on NVIDIA (unaffected by CUDA_VISIBLE_DEVICES),
    with a torch-based fallback for AMD ROCm and Intel XPU.
    Result is cached after the first call.
    """
    global _physical_gpu_count
    if _physical_gpu_count is not None:
        return _physical_gpu_count

    device = get_device()

    if device == DeviceType.CUDA:
        try:
            if IS_ROCM:
                from . import amd as _smi_mod
            else:
                from . import nvidia as _smi_mod
            count = _smi_mod.get_physical_gpu_count()
            if count is not None:
                _physical_gpu_count = count
                return _physical_gpu_count
        except Exception:
            pass
        # SMI tool unavailable or failed -- fall back to torch
        count = _torch_get_physical_gpu_count()
        _physical_gpu_count = count if count is not None else 1
        return _physical_gpu_count

    if device == DeviceType.XPU:
        count = _torch_get_physical_gpu_count()
        _physical_gpu_count = count if count is not None else 1
        return _physical_gpu_count

    if device == DeviceType.MLX:
        _physical_gpu_count = 1
        return _physical_gpu_count

    _physical_gpu_count = 0

    return _physical_gpu_count