def create_multiarch_bundle(code_objects: dict, output_bundle_path: str) -> bool:
    """
    Bundle multiple architecture code objects into a single multi-arch bundle.

    Uses clang-offload-bundler to create a fat binary that HIP runtime can load.
    The runtime automatically selects the correct architecture at load time.

    Args:
        code_objects: Dict mapping architecture to code object path
        output_bundle_path: Path for output bundle

    Returns:
        True if successful
    """
    if not code_objects:
        return False

    os.makedirs(os.path.dirname(output_bundle_path), exist_ok=True)

    try:
        bundler = get_rocm_bundler()
    except RuntimeError:
        return False

    # Build targets and inputs lists for clang-offload-bundler
    targets = ["host-x86_64-unknown-linux-gnu"]

    # We include a dummy host entry to satisfy the bundler format
    inputs = ["/dev/null"]

    for arch, path in sorted(code_objects.items()):
        if not os.path.exists(path):
            continue
        # hipv4 = HIP version 4 code object format
        # amdgcn-amd-amdhsa = target triple for ROCm/HSA runtime
        # arch = specific GPU (gfx90a, gfx942, etc.)
        targets.append(f"hipv4-amdgcn-amd-amdhsa--{arch}")
        inputs.append(path)

    if len(inputs) == 1:  # Only host, no device code
        return False

    cmd = [
        bundler,
        "--type=o",
        # CRITICAL: HIP runtime expects 4096-byte alignment for loading bundles
        # Without this, hipModuleLoadData gives segmentation fault
        "-bundle-align=4096",  # CRITICAL: Required by HIP runtime!
        f"--targets={','.join(targets)}",
    ]

    for input_file in inputs:
        cmd.append(f"--input={input_file}")

    cmd.append(f"--output={output_bundle_path}")

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        if not os.path.exists(output_bundle_path):
            return False

        return True

    except subprocess.CalledProcessError:
        return False