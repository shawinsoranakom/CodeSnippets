def _write_ninja_file_and_build_library(
        name,
        sources: list[str],
        extra_cflags,
        extra_cuda_cflags,
        extra_sycl_cflags,
        extra_ldflags,
        extra_include_paths,
        build_directory: str,
        verbose: bool,
        with_cuda: bool | None,
        with_sycl: bool | None,
        is_standalone: bool = False) -> None:
    verify_ninja_availability()

    compiler = get_cxx_compiler()

    get_compiler_abi_compatibility_and_version(compiler)
    if with_cuda is None:
        with_cuda = any(map(_is_cuda_file, sources))
    if with_sycl is None:
        with_sycl = any(map(_is_sycl_file, sources))
    if with_sycl and with_cuda:
        raise AssertionError(
            "cannot have both SYCL and CUDA files in the same extension"
        )
    extra_ldflags = _prepare_ldflags(
        extra_ldflags or [],
        with_cuda,
        with_sycl,
        verbose,
        is_standalone)
    build_file_path = os.path.join(build_directory, 'build.ninja')
    if verbose:
        logger.debug('Emitting ninja build file %s...', build_file_path)

    # Create build_directory if it does not exist
    if not os.path.exists(build_directory):
        if verbose:
            logger.debug('Creating directory %s...', build_directory)
        # This is like mkdir -p, i.e. will also create parent directories.
        os.makedirs(build_directory, exist_ok=True)

    # NOTE: Emitting a new ninja build file does not cause re-compilation if
    # the sources did not change, so it's ok to re-emit (and it's fast).
    _write_ninja_file_to_build_library(
        path=build_file_path,
        name=name,
        sources=sources,
        extra_cflags=extra_cflags or [],
        extra_cuda_cflags=extra_cuda_cflags or [],
        extra_sycl_cflags=extra_sycl_cflags or [],
        extra_ldflags=extra_ldflags or [],
        extra_include_paths=extra_include_paths or [],
        with_cuda=with_cuda,
        with_sycl=with_sycl,
        is_standalone=is_standalone)

    if verbose:
        logger.info('Building extension module %s...', name)
    _run_ninja_build(
        build_directory,
        verbose,
        error_prefix=f"Error building extension '{name}'")