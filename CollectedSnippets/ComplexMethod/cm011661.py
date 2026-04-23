def get_device_tflops(dtype: torch.dtype) -> float:
    """
    We don't want to throw errors in this function. First check to see if the device is in device_info.py,
    then fall back to the inaccurate triton estimation.
    """
    ds_tops = datasheet_tops(
        dtype, is_tf32=torch.backends.cuda.matmul.fp32_precision == "tf32"
    )
    if ds_tops is not None:
        return ds_tops

    from triton.testing import get_max_simd_tflops, get_max_tensorcore_tflops

    SM80OrLater = torch.cuda.is_available() and torch.cuda.get_device_capability() >= (
        8,
        0,
    )

    assert dtype in (torch.float16, torch.bfloat16, torch.float32)

    if inspect.signature(get_max_simd_tflops).parameters.get("clock_rate"):
        # Triton API change in https://github.com/triton-lang/triton/pull/2293
        from torch._utils_internal import max_clock_rate

        sm_clock = max_clock_rate()
        if dtype in (torch.float16, torch.bfloat16) and SM80OrLater:
            return get_max_tensorcore_tflops(dtype, sm_clock)

        if torch.backends.cuda.matmul.fp32_precision == "tf32":
            return get_max_tensorcore_tflops(torch.float32, sm_clock)
        else:
            return get_max_simd_tflops(torch.float32, sm_clock)
    else:
        if dtype in (torch.float16, torch.bfloat16) and SM80OrLater:
            return get_max_tensorcore_tflops(dtype)

        if torch.backends.cuda.matmul.fp32_precision == "tf32":
            return get_max_tensorcore_tflops(torch.float32)
        else:
            return get_max_simd_tflops(torch.float32)