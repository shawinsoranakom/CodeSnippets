def _find_rocm_home() -> str | None:
    """Find the ROCm install path."""
    # Guess #1
    rocm_home = os.environ.get('ROCM_HOME') or os.environ.get('ROCM_PATH')
    if rocm_home is None:
        # Guess #2
        hipcc_path = shutil.which('hipcc')
        if hipcc_path is not None:
            rocm_home = os.path.dirname(os.path.dirname(
                os.path.realpath(hipcc_path)))
            # can be either <ROCM_HOME>/hip/bin/hipcc or <ROCM_HOME>/bin/hipcc
            if os.path.basename(rocm_home) == 'hip':
                rocm_home = os.path.dirname(rocm_home)
        else:
            # Guess #3
            fallback_path = '/opt/rocm'
            if os.path.exists(fallback_path):
                rocm_home = fallback_path
    if rocm_home and torch.version.hip is None:
        logger.warning("No ROCm runtime is found, using ROCM_HOME='%s'", rocm_home)
    return rocm_home