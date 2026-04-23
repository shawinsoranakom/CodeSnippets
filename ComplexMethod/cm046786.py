def apply_gpu_ids(gpu_ids) -> None:
    if gpu_ids is None:
        return

    # Empty list means "no GPUs visible" -- treat the same as None
    # (inherit parent) to avoid setting CUDA_VISIBLE_DEVICES="" which
    # disables CUDA entirely and crashes downstream torch calls.
    if isinstance(gpu_ids, (list, tuple)) and len(gpu_ids) == 0:
        return

    global _visible_gpu_count

    if isinstance(gpu_ids, (list, tuple)):
        value = ",".join(str(g) for g in gpu_ids)
    else:
        value = str(gpu_ids)

    os.environ["CUDA_VISIBLE_DEVICES"] = value
    # Keep ROCm visibility env vars in sync so _get_parent_visible_gpu_spec()
    # picks up the narrowed set on AMD systems. Workers can call
    # apply_gpu_ids() before detect_hardware() runs (so IS_ROCM is still
    # its default False), so also mirror the selection whenever the
    # parent process already set a ROCm visibility variable -- that
    # way a downstream ROCm process inherits the narrowed mask even
    # before Studio's hardware detection has classified the host.
    _inherits_rocm_visibility = (
        "HIP_VISIBLE_DEVICES" in os.environ or "ROCR_VISIBLE_DEVICES" in os.environ
    )
    if IS_ROCM or _inherits_rocm_visibility:
        os.environ["HIP_VISIBLE_DEVICES"] = value
        os.environ["ROCR_VISIBLE_DEVICES"] = value
    _visible_gpu_count = None
    if IS_ROCM or _inherits_rocm_visibility:
        logger.info("Applied gpu_ids: CUDA_VISIBLE_DEVICES='%s' (rocm)", value)
    else:
        logger.info("Applied gpu_ids: CUDA_VISIBLE_DEVICES='%s'", value)