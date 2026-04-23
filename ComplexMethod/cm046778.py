def _get_parent_visible_gpu_spec() -> Dict[str, Any]:
    # ROCm uses HIP_VISIBLE_DEVICES / ROCR_VISIBLE_DEVICES in addition to
    # CUDA_VISIBLE_DEVICES (which HIP also respects).  Check ROCm-specific
    # env vars first so multi-GPU AMD setups are handled correctly.
    # Use explicit None checks (not `or`) so empty string "" is honoured
    # as "no visible GPUs" rather than falling through to CUDA_VISIBLE_DEVICES.
    cuda_visible = None
    if IS_ROCM:
        hip_vis = os.environ.get("HIP_VISIBLE_DEVICES")
        rocr_vis = os.environ.get("ROCR_VISIBLE_DEVICES")
        if hip_vis is not None:
            cuda_visible = hip_vis
        elif rocr_vis is not None:
            cuda_visible = rocr_vis
    if cuda_visible is None:
        cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")

    if cuda_visible is None:
        return {
            "raw": None,
            "numeric_ids": list(range(get_physical_gpu_count())),
            "supports_explicit_gpu_ids": True,
        }

    cuda_visible = cuda_visible.strip()
    if cuda_visible == "" or cuda_visible == "-1":
        return {
            "raw": cuda_visible,
            "numeric_ids": [],
            "supports_explicit_gpu_ids": True,
        }

    tokens = [value.strip() for value in cuda_visible.split(",") if value.strip()]
    try:
        numeric_ids = [int(value) for value in tokens]
    except ValueError:
        return {
            "raw": cuda_visible,
            "numeric_ids": None,
            "supports_explicit_gpu_ids": False,
        }

    return {
        "raw": cuda_visible,
        "numeric_ids": numeric_ids,
        "supports_explicit_gpu_ids": True,
    }