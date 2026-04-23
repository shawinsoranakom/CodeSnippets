def get_compiler_abi_compatibility_and_version(compiler) -> tuple[bool, TorchVersion]:
    """
    Determine if the given compiler is ABI-compatible with PyTorch alongside its version.

    Args:
        compiler (str): The compiler executable name to check (e.g. ``g++``).
            Must be executable in a shell process.

    Returns:
        A tuple that contains a boolean that defines if the compiler is (likely) ABI-incompatible with PyTorch,
        followed by a `TorchVersion` string that contains the compiler version separated by dots.
    """
    if not _is_binary_build():
        return (True, TorchVersion('0.0.0'))
    if os.environ.get('TORCH_DONT_CHECK_COMPILER_ABI') in ['ON', '1', 'YES', 'TRUE', 'Y']:
        return (True, TorchVersion('0.0.0'))

    # First check if the compiler is one of the expected ones for the particular platform.
    if not check_compiler_ok_for_platform(compiler):
        logger.warning(WRONG_COMPILER_WARNING, compiler, _accepted_compilers_for_platform()[0], sys.platform, _accepted_compilers_for_platform()[0], compiler, compiler)
        return (False, TorchVersion('0.0.0'))

    if IS_MACOS:
        # There is no particular minimum version we need for clang, so we're good here.
        return (True, TorchVersion('0.0.0'))
    try:
        if IS_LINUX:
            minimum_required_version = MINIMUM_GCC_VERSION
            compiler_info = subprocess.check_output([compiler, '-dumpfullversion', '-dumpversion'])
        else:
            minimum_required_version = MINIMUM_MSVC_VERSION
            compiler_info = subprocess.check_output(compiler, stderr=subprocess.STDOUT)
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', compiler_info.decode(*SUBPROCESS_DECODE_ARGS).strip())
        version = ['0', '0', '0'] if match is None else list(match.groups())
    except (subprocess.CalledProcessError, OSError):
        logger.warning('Error checking compiler version for %s', compiler, exc_info=True)
        return (False, TorchVersion('0.0.0'))

    # convert alphanumeric string to numeric string
    # amdclang++ returns str like 0.0.0git, others return 0.0.0
    numeric_version = [re.sub(r'\D', '', v) for v in version]

    if tuple(map(int, numeric_version)) >= minimum_required_version:
        return (True, TorchVersion('.'.join(numeric_version)))

    compiler = f'{compiler} {".".join(numeric_version)}'
    logger.warning(ABI_INCOMPATIBILITY_WARNING, compiler)

    return (False, TorchVersion('.'.join(numeric_version)))