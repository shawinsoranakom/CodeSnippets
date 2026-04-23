def _in_unstable_openblas_configuration():
    """Return True if in an unstable configuration for OpenBLAS"""

    # Import libraries which might load OpenBLAS.
    import numpy  # noqa: F401
    import scipy  # noqa: F401

    modules_info = _get_threadpool_controller().info()

    open_blas_used = any(info["internal_api"] == "openblas" for info in modules_info)
    if not open_blas_used:
        return False

    # OpenBLAS 0.3.16 fixed instability for arm64, see:
    # https://github.com/xianyi/OpenBLAS/blob/1b6db3dbba672b4f8af935bd43a1ff6cff4d20b7/Changelog.txt#L56-L58
    openblas_arm64_stable_version = parse_version("0.3.16")
    for info in modules_info:
        if info["internal_api"] != "openblas":
            continue
        openblas_version = info.get("version")
        openblas_architecture = info.get("architecture")
        if openblas_version is None or openblas_architecture is None:
            # Cannot be sure that OpenBLAS is good enough. Assume unstable:
            return True  # pragma: no cover
        if (
            openblas_architecture == "neoversen1"
            and parse_version(openblas_version) < openblas_arm64_stable_version
        ):
            # See discussions in https://github.com/numpy/numpy/issues/19411
            return True  # pragma: no cover
    return False