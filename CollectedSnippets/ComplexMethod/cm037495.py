def _sync_hip_cuda_env_vars():
    """Ensure HIP_VISIBLE_DEVICES and CUDA_VISIBLE_DEVICES are consistent.
    Treats empty string as unset. Raises on genuine conflicts."""
    hip_val = os.environ.get("HIP_VISIBLE_DEVICES") or None
    cuda_val = os.environ.get("CUDA_VISIBLE_DEVICES") or None

    if hip_val is not None and cuda_val is not None:
        if hip_val != cuda_val:
            raise ValueError(
                f"Inconsistent GPU visibility env vars: "
                f"HIP_VISIBLE_DEVICES='{hip_val}' vs "
                f"CUDA_VISIBLE_DEVICES='{cuda_val}'. "
                f"Please set only one, or ensure they match."
            )
    elif hip_val is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = hip_val
    elif cuda_val is not None:
        os.environ["HIP_VISIBLE_DEVICES"] = cuda_val