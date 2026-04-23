def disable_broken_vllm(error = None):
    """Disable vLLM dynamically when its shared library is ABI-broken."""
    global VLLM_BROKEN
    if VLLM_BROKEN:
        _install_vllm_blocker()
        return True

    failure = error
    if failure is None:
        try:
            if importlib.util.find_spec("vllm") is None:
                return False
        except Exception:
            return False

        try:
            import vllm  # noqa: F401

            return False
        except Exception as import_error:
            failure = import_error

    if not _is_broken_vllm_error(failure):
        return False

    VLLM_BROKEN = True
    _clear_vllm_modules()
    _install_vllm_blocker()
    cuda_msg = _get_vllm_cuda_mismatch_message(failure)
    if cuda_msg:
        logger.warning(cuda_msg)
    else:
        logger.warning(
            "Unsloth: Detected broken vLLM binary extension; "
            "disabling vLLM imports and continuing import.\n"
            "Please reinstall via `uv pip install unsloth vllm torchvision torchaudio "
            "--torch-backend=auto`."
        )
    return True