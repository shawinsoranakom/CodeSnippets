def check_wheel_platform_tag() -> None:
    """Validate that wheel Tags in WHEEL metadata match the expected platform.

    Mode 1: PYTORCH_FINAL_PACKAGE_DIR set → read .whl file (strict, raises on mismatch)
    Mode 2: No wheel dir → read from installed torch package (soft, prints warnings)
    """
    wheel_dir = os.getenv("PYTORCH_FINAL_PACKAGE_DIR", "")

    target_os = os.getenv("TARGET_OS", sys.platform)
    if target_os == "linux" and platform.machine() == "aarch64":
        target_os = "linux-aarch64"
    expected_python = f"cp{sys.version_info.major}{sys.version_info.minor}"
    import sysconfig

    abiflags = getattr(sys, "abiflags", "")
    if not abiflags and (
        os.getenv("MATRIX_PYTHON_VERSION", "").endswith("t")
        or bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
        or not getattr(sys, "_is_gil_enabled", lambda: True)()
    ):
        abiflags = "t"
    expected_abi = f"cp{sys.version_info.major}{sys.version_info.minor}{abiflags}"
    print(f"Expected ABI tag: {expected_abi}")

    platform_pattern = EXPECTED_PLATFORM_TAGS.get(target_os)
    if not platform_pattern:
        print(
            f"No expected platform pattern for TARGET_OS={target_os}, "
            "skipping wheel tag check"
        )
        return

    # Mode 1: Read from .whl file
    if wheel_dir and os.path.isdir(wheel_dir):
        whls = list(Path(wheel_dir).glob("torch-*.whl"))
        if not whls:
            print(f"No torch wheel found in {wheel_dir}, skipping wheel tag check")
            return
        if len(whls) > 1:
            raise RuntimeError(
                f"Expected exactly one torch wheel in {wheel_dir}, "
                f"found {len(whls)}: {[w.name for w in whls]}"
            )
        whl = whls[0]
        print(f"Checking wheel platform tag for: {whl.name}")
        tags = _extract_wheel_tags(whl)
        source = whl.name
    else:
        # Mode 2: Read from installed package (soft)
        print("PYTORCH_FINAL_PACKAGE_DIR not set, reading from installed torch package")
        try:
            tags = _extract_installed_wheel_tags("torch")
            source = "installed torch"
        except Exception as e:
            print(f"Could not read installed torch metadata: {e}, skipping")
            return

    if not tags:
        raise RuntimeError(f"No Tag found in WHEEL metadata of {source}")

    for tag_str in tags:
        parts = tag_str.split("-")
        if len(parts) != 3:
            msg = (
                f"Malformed wheel tag '{tag_str}' in {source}, "
                f"expected format: <python>-<abi>-<platform>"
            )
            raise RuntimeError(msg)

        python_tag, abi_tag, platform_tag = parts

        print(f"Checking tag: {tag_str} (from {source})")
        if python_tag != expected_python:
            msg: str = (
                f"Python tag mismatch in {source}: "
                f"got '{python_tag}', expected '{expected_python}'"
            )
            raise RuntimeError(msg)

        if abi_tag != expected_abi:
            msg = (
                f"ABI tag mismatch in {source}: "
                f"got '{abi_tag}', expected '{expected_abi}'"
            )
            raise RuntimeError(msg)

        if not re.search(platform_pattern, platform_tag):
            msg = (
                f"Platform tag mismatch in {source}: "
                f"got '{platform_tag}', expected pattern matching "
                f"'{platform_pattern}' for TARGET_OS={target_os}"
            )
            raise RuntimeError(msg)

    print(f"OK: Wheel tag(s) valid for {source}: {', '.join(tags)}")