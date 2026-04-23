def _check_cuda_version(compiler_name: str, compiler_version: TorchVersion) -> None:
    if not CUDA_HOME:
        raise RuntimeError(CUDA_NOT_FOUND_MESSAGE)

    nvcc = os.path.join(CUDA_HOME, 'bin', 'nvcc.exe' if IS_WINDOWS else 'nvcc')
    if not os.path.exists(nvcc):
        raise FileNotFoundError(f"nvcc not found at '{nvcc}'. Ensure CUDA path '{CUDA_HOME}' is correct.")

    cuda_version_str = subprocess.check_output([nvcc, '--version']).strip().decode(*SUBPROCESS_DECODE_ARGS)
    cuda_version = re.search(r'release (\d+[.]\d+)', cuda_version_str)
    if cuda_version is None:
        return

    cuda_str_version = cuda_version.group(1)
    cuda_ver = Version(cuda_str_version)
    if torch.version.cuda is None:
        return

    torch_cuda_version = Version(torch.version.cuda)
    if cuda_ver != torch_cuda_version:
        # major/minor attributes are only available in setuptools>=49.4.0
        if getattr(cuda_ver, "major", None) is None:
            raise ValueError("setuptools>=49.4.0 is required")
        if cuda_ver.major != torch_cuda_version.major:
            raise RuntimeError(CUDA_MISMATCH_MESSAGE, cuda_str_version, torch.version.cuda)
        logger.warning(CUDA_MISMATCH_WARN, cuda_str_version, torch.version.cuda)

    if not (sys.platform.startswith('linux') and
            os.environ.get('TORCH_DONT_CHECK_COMPILER_ABI') not in ['ON', '1', 'YES', 'TRUE', 'Y'] and
            _is_binary_build()):
        return

    cuda_compiler_bounds: VersionMap = CUDA_CLANG_VERSIONS if compiler_name.startswith('clang') else CUDA_GCC_VERSIONS

    if cuda_str_version not in cuda_compiler_bounds:
        logger.warning('There are no %s version bounds defined for CUDA version %s', compiler_name, cuda_str_version)
    else:
        min_compiler_version, max_excl_compiler_version = cuda_compiler_bounds[cuda_str_version]
        # Special case for 11.4.0, which has lower compiler bounds than 11.4.1
        if "V11.4.48" in cuda_version_str and cuda_compiler_bounds == CUDA_GCC_VERSIONS:
            max_excl_compiler_version = (11, 0)
        min_compiler_version_str = '.'.join(map(str, min_compiler_version))
        max_excl_compiler_version_str = '.'.join(map(str, max_excl_compiler_version))

        version_bound_str = f'>={min_compiler_version_str}, <{max_excl_compiler_version_str}'

        if compiler_version < TorchVersion(min_compiler_version_str):
            raise RuntimeError(
                f'The current installed version of {compiler_name} ({compiler_version}) is less '
                f'than the minimum required version by CUDA {cuda_str_version} ({min_compiler_version_str}). '
                f'Please make sure to use an adequate version of {compiler_name} ({version_bound_str}).'
            )
        if compiler_version >= TorchVersion(max_excl_compiler_version_str):
            raise RuntimeError(
                f'The current installed version of {compiler_name} ({compiler_version}) is greater '
                f'than the maximum required version by CUDA {cuda_str_version}. '
                f'Please make sure to use an adequate version of {compiler_name} ({version_bound_str}).'
            )