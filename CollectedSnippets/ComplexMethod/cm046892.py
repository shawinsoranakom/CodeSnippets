def torchvision_compatibility_check():
    # Allow skipping via environment variable for custom environments
    if os.environ.get("UNSLOTH_SKIP_TORCHVISION_CHECK", "0").lower() in ("1", "true"):
        return

    if importlib.util.find_spec("torch") is None:
        raise ImportError("Unsloth: torch not found. Please install torch first.")
    if importlib.util.find_spec("torchvision") is None:
        return

    try:
        torch_version_raw = importlib_version("torch")
        torchvision_version_raw = importlib_version("torchvision")
    except Exception:
        return

    try:
        torch_v = Version(torch_version_raw)
        tv_v = Version(torchvision_version_raw)
    except Exception:
        return

    # Known compatibility table (ground truth, takes precedence over formula).
    # See https://pytorch.org/get-started/previous-versions/
    TORCH_TORCHVISION_COMPAT = {
        (2, 9): (0, 24),
        (2, 8): (0, 23),
        (2, 7): (0, 22),
        (2, 6): (0, 21),
        (2, 5): (0, 20),
        (2, 4): (0, 19),
    }

    # Extract major.minor from the parsed version
    torch_release = torch_v.release
    if len(torch_release) < 2:
        return
    torch_major, torch_minor = torch_release[0], torch_release[1]

    # Try known table first, then fall back to formula for forward compatibility
    required = TORCH_TORCHVISION_COMPAT.get((torch_major, torch_minor))

    if required is None:
        required = _infer_required_torchvision(torch_major, torch_minor)

    if required is None:
        return

    required_tv_str = f"{required[0]}.{required[1]}.0"

    if tv_v >= Version(required_tv_str):
        logger.info(
            f"Unsloth: torch=={torch_version_raw} and "
            f"torchvision=={torchvision_version_raw} are compatible."
        )
        return

    # Version mismatch detected
    message = (
        f"Unsloth: torch=={torch_version_raw} requires "
        f"torchvision>={required_tv_str}, "
        f"but found torchvision=={torchvision_version_raw}. "
        f'Try updating torchvision via `pip install --upgrade "torchvision>={required_tv_str}"`. '
        f"Please refer to https://pytorch.org/get-started/previous-versions/ "
        f"for more information."
    )

    is_custom = _is_custom_torch_build(torch_version_raw) or _is_custom_torch_build(
        torchvision_version_raw
    )

    # Detect nightly/dev/alpha/beta/rc builds from the raw version string.
    # These often have version mismatches that are expected.
    _pre_tags = (".dev", "a0", "b0", "rc", "alpha", "beta", "nightly")
    is_prerelease = any(t in torch_version_raw for t in _pre_tags) or any(
        t in torchvision_version_raw for t in _pre_tags
    )

    # Only downgrade to warning for custom/source or prerelease builds.
    # Stable mismatches should fail fast to prevent runtime operator errors.
    if is_custom or is_prerelease:
        reason = "custom/source build" if is_custom else "pre-release build"
        logger.warning(
            f"{message}\n"
            f"Detected a {reason}. "
            f"Continuing with a warning. "
            f"Set UNSLOTH_SKIP_TORCHVISION_CHECK=1 to silence this."
        )
        return

    raise ImportError(message)