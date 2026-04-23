def _jit_compile(name,
                 sources,
                 extra_cflags,
                 extra_cuda_cflags,
                 extra_sycl_cflags,
                 extra_ldflags,
                 extra_include_paths,
                 build_directory: str,
                 verbose: bool,
                 with_cuda: bool | None,
                 with_sycl: bool | None,
                 is_python_module,
                 is_standalone,
                 keep_intermediates=True) -> types.ModuleType | str:
    if is_python_module and is_standalone:
        raise ValueError("`is_python_module` and `is_standalone` are mutually exclusive.")

    if with_cuda is None:
        with_cuda = any(map(_is_cuda_file, sources))
    with_cudnn = any('cudnn' in f for f in extra_ldflags or [])
    if with_sycl is None:
        with_sycl = any(map(_is_sycl_file, sources))
    if with_sycl and with_cuda:
        raise AssertionError(
            "cannot have both SYCL and CUDA files in the same extension"
        )
    old_version = JIT_EXTENSION_VERSIONER.get_version(name)
    version = JIT_EXTENSION_VERSIONER.bump_version_if_changed(
        name,
        sources,
        build_arguments=[extra_cflags, extra_cuda_cflags, extra_ldflags, extra_include_paths],
        build_directory=build_directory,
        with_cuda=with_cuda,
        with_sycl=with_sycl,
        is_python_module=is_python_module,
        is_standalone=is_standalone,
    )
    if version > 0:
        if version != old_version and verbose:
            logger.info('The input conditions for extension module %s have changed.', name)
            logger.info('Bumping to version %s and re-building as %s_v%s...', version, name, version)
        name = f'{name}_v{version}'

    baton = FileBaton(os.path.join(build_directory, 'lock'))
    if baton.try_acquire():
        try:
            if version != old_version:
                if IS_HIP_EXTENSION and (with_cuda or with_cudnn):
                    from .hipify import hipify_python
                    from .hipify.hipify_python import GeneratedFileCleaner
                    clean_ctx_mgr = GeneratedFileCleaner(keep_intermediates=keep_intermediates)
                else:
                    import contextlib
                    hipify_python = None  # type: ignore[assignment]
                    clean_ctx_mgr = contextlib.nullcontext()
                with clean_ctx_mgr as clean_ctx:
                    if IS_HIP_EXTENSION and (with_cuda or with_cudnn):
                        assert hipify_python is not None  # noqa: S101
                        hipify_result = hipify_python.hipify(
                            project_directory=build_directory,
                            output_directory=build_directory,
                            header_include_dirs=(extra_include_paths if extra_include_paths is not None else []),
                            extra_files=[os.path.abspath(s) for s in sources],
                            ignores=[_join_rocm_home('*'), os.path.join(_TORCH_PATH, '*')],  # no need to hipify ROCm or PyTorch headers
                            show_detailed=verbose,
                            show_progress=verbose,
                            is_pytorch_extension=True,
                            clean_ctx=clean_ctx
                        )

                        hipified_sources = set()
                        for source in sources:
                            s_abs = os.path.abspath(source)
                            if s_abs in hipify_result and hipify_result[s_abs].hipified_path is not None:
                                hipified_s_abs = hipify_result[s_abs].hipified_path
                            else:
                                hipified_s_abs = s_abs
                            hipified_sources.add(hipified_s_abs)
                        sources = list(hipified_sources)

                    _write_ninja_file_and_build_library(
                        name=name,
                        sources=sources,
                        extra_cflags=extra_cflags or [],
                        extra_cuda_cflags=extra_cuda_cflags or [],
                        extra_sycl_cflags=extra_sycl_cflags or [],
                        extra_ldflags=extra_ldflags or [],
                        extra_include_paths=extra_include_paths or [],
                        build_directory=build_directory,
                        verbose=verbose,
                        with_cuda=with_cuda,
                        with_sycl=with_sycl,
                        is_standalone=is_standalone)
            elif verbose:
                logger.debug('No modifications detected for re-loaded extension module %s, skipping build step...', name)
        finally:
            baton.release()
    else:
        baton.wait()

    if verbose:
        logger.info('Loading extension module %s...', name)

    if is_standalone:
        return _get_exec_path(name, build_directory)

    return _import_module_from_library(name, build_directory, is_python_module)