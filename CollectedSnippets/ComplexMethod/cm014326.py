def _write_ninja_file_and_compile_objects(
        sources: list[str],
        objects,
        cflags,
        post_cflags,
        cuda_cflags,
        cuda_post_cflags,
        cuda_dlink_post_cflags,
        sycl_cflags,
        sycl_post_cflags,
        sycl_dlink_post_cflags,
        build_directory: str,
        verbose: bool,
        with_cuda: bool | None,
        with_sycl: bool | None) -> None:
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
    build_file_path = os.path.join(build_directory, 'build.ninja')
    if verbose:
        logger.debug('Emitting ninja build file %s...', build_file_path)

    # Create build_directory if it does not exist
    if not os.path.exists(build_directory):
        if verbose:
            logger.debug('Creating directory %s...', build_directory)
        # This is like mkdir -p, i.e. will also create parent directories.
        os.makedirs(build_directory, exist_ok=True)

    _write_ninja_file(
        path=build_file_path,
        cflags=cflags,
        post_cflags=post_cflags,
        cuda_cflags=cuda_cflags,
        cuda_post_cflags=cuda_post_cflags,
        cuda_dlink_post_cflags=cuda_dlink_post_cflags,
        sycl_cflags=sycl_cflags,
        sycl_post_cflags=sycl_post_cflags,
        sycl_dlink_post_cflags=sycl_dlink_post_cflags,
        sources=sources,
        objects=objects,
        ldflags=None,
        library_target=None,
        with_cuda=with_cuda,
        with_sycl=with_sycl)
    if verbose:
        logger.info('Compiling objects...')
    _run_ninja_build(
        build_directory,
        verbose,
        # It would be better if we could tell users the name of the extension
        # that failed to build but there isn't a good way to get it here.
        error_prefix='Error compiling objects for extension')