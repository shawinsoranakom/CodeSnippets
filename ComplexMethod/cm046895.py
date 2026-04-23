def _is_rocm_torch_build() -> bool:
    # Most official ROCm wheels include a local version suffix like +rocmX.Y.
    # Some custom/source builds do not, so we fall back to runtime hints.
    try:
        torch_version_raw = str(importlib_version("torch")).lower()
        if "rocm" in torch_version_raw:
            _log_rocm_detection(
                "Unsloth: ROCm detection matched torch version tag (+rocm)."
            )
            return True
    except Exception:
        pass

    # Environment hints commonly present on ROCm runtimes.
    for key in _ROCM_ENV_HINT_KEYS:
        value = os.environ.get(key, "")
        if isinstance(value, str) and value.strip():
            _log_rocm_detection(
                f"Unsloth: ROCm detection matched environment key `{key}`."
            )
            return True

    # Filesystem / driver hints for ROCm stacks.
    for path in _ROCM_PATH_HINTS:
        try:
            if path.exists():
                _log_rocm_detection(
                    f"Unsloth: ROCm detection matched filesystem hint `{path}`."
                )
                return True
        except Exception:
            continue

    _log_rocm_detection("Unsloth: ROCm detection did not match any known hints.")
    return False