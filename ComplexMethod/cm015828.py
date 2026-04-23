def _fix_fp8_dtype_for_rocm(
    dtype: torch.dtype | list[torch.dtype] | tuple[torch.dtype], device
) -> torch.dtype | list[torch.dtype] | tuple[torch.dtype]:
    # This function is used to change FP8 data types
    # with MI300 supported FP8 types if device is GPU:
    #    e4m3fn -> e4m3fnuz
    #    e5m2   -> e5m2fnuz
    # Supports single, tuple and list of dtypes
    # Keeps the same test name for CUDA and ROCm
    # Also it allows to enable FP8 inductor tests for CPU
    if (
        torch.version.hip
        and (_is_cuda_device(device))
        and ("gfx94" in torch.cuda.get_device_properties(0).gcnArchName.split(":")[0])
    ):
        # MI300 uses different float8 dtypes
        if isinstance(dtype, tuple):
            return tuple(_fix_fp8_dtype_for_rocm(x, device) for x in dtype)
        if isinstance(dtype, list):
            return [_fix_fp8_dtype_for_rocm(x, device) for x in dtype]
        if dtype == torch.float8_e4m3fn:
            return torch.float8_e4m3fnuz
        elif dtype == torch.float8_e5m2:
            return torch.float8_e5m2fnuz
    return dtype