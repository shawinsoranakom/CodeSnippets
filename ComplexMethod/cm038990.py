def get_custom_wheel_versions(install_dir: str) -> dict[str, str]:
    """
    Read /install directory and extract versions of custom wheels.

    Returns:
        Dict mapping package names to exact versions
    """
    install_path = Path(install_dir)
    if not install_path.exists():
        print(f"ERROR: Install directory not found: {install_dir}", file=sys.stderr)
        sys.exit(1)

    versions = {}

    # Map wheel prefixes to package names
    # IMPORTANT: Use dashes to avoid matching substrings
    #            (e.g., 'torch' would match 'torchvision')
    # ORDER MATTERS: This order is preserved when pinning dependencies
    #               in requirements files
    package_mapping = [
        ("torch-", "torch"),  # Match torch- (not torchvision)
        ("triton-", "triton"),  # Match triton- (not triton_kernels)
        ("triton_kernels-", "triton-kernels"),  # Match triton_kernels-
        ("torchvision-", "torchvision"),  # Match torchvision-
        ("torchaudio-", "torchaudio"),  # Match torchaudio-
        ("amdsmi-", "amdsmi"),  # Match amdsmi-
        ("flash_attn-", "flash-attn"),  # Match flash_attn-
        ("amd_aiter-", "amd-aiter"),  # Match amd_aiter-
    ]

    for wheel_file in install_path.glob("*.whl"):
        wheel_name = wheel_file.name

        for prefix, package_name in package_mapping:
            if wheel_name.startswith(prefix):
                try:
                    version = extract_version_from_wheel(wheel_name)
                    versions[package_name] = version
                    print(f"Found {package_name}=={version}", file=sys.stderr)
                except Exception as e:
                    print(
                        f"WARNING: Could not extract version from {wheel_name}: {e}",
                        file=sys.stderr,
                    )
                break

    # Return versions in the order defined by package_mapping
    ordered_versions = {}
    for _, package_name in package_mapping:
        if package_name in versions:
            ordered_versions[package_name] = versions[package_name]
    return ordered_versions