def autocast(disable=False):
    if disable:
        return contextlib.nullcontext()

    if force_fp16:
        # No casting during inference if force_fp16 is enabled.
        # All tensor dtype conversion happens before inference.
        return contextlib.nullcontext()

    if fp8 and device==cpu:
        return torch.autocast("cpu", dtype=torch.bfloat16, enabled=True)

    if fp8 and dtype_inference == torch.float32:
        return manual_cast(dtype)

    if dtype == torch.float32 or dtype_inference == torch.float32:
        return contextlib.nullcontext()

    if has_xpu() or has_mps() or cuda_no_autocast():
        return manual_cast(dtype)

    return torch.autocast("cuda")