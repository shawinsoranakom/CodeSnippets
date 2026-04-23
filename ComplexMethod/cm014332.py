def _write_ninja_file_to_build_library(path,
                                       name,
                                       sources,
                                       extra_cflags,
                                       extra_cuda_cflags,
                                       extra_sycl_cflags,
                                       extra_ldflags,
                                       extra_include_paths,
                                       with_cuda,
                                       with_sycl,
                                       is_standalone) -> None:
    extra_cflags = [flag.strip() for flag in extra_cflags]
    extra_cuda_cflags = [flag.strip() for flag in extra_cuda_cflags]
    extra_sycl_cflags = [flag.strip() for flag in extra_sycl_cflags]
    extra_ldflags = [flag.strip() for flag in extra_ldflags]
    extra_include_paths = [flag.strip() for flag in extra_include_paths]

    # Turn into absolute paths so we can emit them into the ninja build
    # file wherever it is.
    user_includes = [os.path.abspath(file) for file in extra_include_paths]

    # include_paths() gives us the location of torch/extension.h
    # TODO generalize with_cuda as specific device type.
    if with_cuda:
        system_includes = include_paths("cuda")
    elif with_sycl:
        system_includes = include_paths("xpu")
    else:
        system_includes = include_paths("cpu")
    # sysconfig.get_path('include') gives us the location of Python.h
    # Explicitly specify 'posix_prefix' scheme on non-Windows platforms to workaround error on some MacOS
    # installations where default `get_path` points to non-existing `/Library/Python/M.m/include` folder
    python_include_path = sysconfig.get_path('include', scheme='nt' if IS_WINDOWS else 'posix_prefix')
    if python_include_path is not None:
        system_includes.append(python_include_path)

    common_cflags = []
    if not is_standalone:
        common_cflags.append(f'-DTORCH_EXTENSION_NAME={name}')
        common_cflags.append('-DTORCH_API_INCLUDE_EXTENSION_H')

    # Windows does not understand `-isystem` and quotes flags later.
    if IS_WINDOWS:
        common_cflags += [f'-I{include}' for include in user_includes + system_includes]
    else:
        common_cflags += [f'-I{shlex.quote(include)}' for include in user_includes]
        common_cflags += [f'-isystem {shlex.quote(include)}' for include in system_includes]

    if IS_WINDOWS:
        COMMON_HIP_FLAGS.extend(['-fms-runtime-lib=dll'])
        cflags = common_cflags + ['/std:c++20'] + extra_cflags
        cflags += COMMON_MSVC_FLAGS + (COMMON_HIP_FLAGS if IS_HIP_EXTENSION else [])
        cflags = _nt_quote_args(cflags)
    else:
        cflags = common_cflags + ['-fPIC', '-std=c++20'] + extra_cflags

    if with_cuda and IS_HIP_EXTENSION:
        cuda_flags = ['-DWITH_HIP'] + common_cflags + extra_cflags + COMMON_HIP_FLAGS + COMMON_HIPCC_FLAGS
        cuda_flags = cuda_flags + ['-std=c++20']
        cuda_flags += _get_rocm_arch_flags(cuda_flags)
        cuda_flags += extra_cuda_cflags
        if IS_WINDOWS:
            cuda_flags = _nt_quote_args(cuda_flags)
    elif with_cuda:
        cuda_flags = common_cflags + COMMON_NVCC_FLAGS + _get_cuda_arch_flags(extra_cuda_cflags)
        if IS_WINDOWS:
            for flag in COMMON_MSVC_FLAGS:
                cuda_flags = ['-Xcompiler', flag] + cuda_flags
            for ignore_warning in MSVC_IGNORE_CUDAFE_WARNINGS:
                cuda_flags = ['-Xcudafe', '--diag_suppress=' + ignore_warning] + cuda_flags
            cuda_flags = cuda_flags + ['-std=c++20']
            cuda_flags = _nt_quote_args(cuda_flags)
            cuda_flags += _nt_quote_args(extra_cuda_cflags)
        else:
            cuda_flags += ['--compiler-options', "'-fPIC'"]
            cuda_flags += extra_cuda_cflags
            if not any(flag.startswith('-std=') for flag in cuda_flags):
                cuda_flags.append('-std=c++20')
            cc_env = os.getenv("CC")
            if cc_env is not None:
                cuda_flags = ['-ccbin', cc_env] + cuda_flags
    else:
        cuda_flags = None

    if with_sycl:
        sycl_cflags = cflags + _COMMON_SYCL_FLAGS
        sycl_cflags += extra_sycl_cflags
        _append_sycl_targets_if_missing(sycl_cflags)
        _append_sycl_std_if_no_std_present(sycl_cflags)
        host_cflags = cflags
        # escaping quoted arguments to pass them thru SYCL compiler
        icpx_version = _get_icpx_version()
        if int(icpx_version) < 20250200:
            host_cflags = [item.replace('\\"', '\\\\"') for item in host_cflags]

        sycl_cflags += _wrap_sycl_host_flags(host_cflags)
        sycl_dlink_post_cflags = _SYCL_DLINK_FLAGS.copy()
        sycl_dlink_post_cflags += _get_sycl_device_flags(sycl_cflags)
    else:
        sycl_cflags = None
        sycl_dlink_post_cflags = None

    def object_file_path(source_file: str) -> str:
        # '/path/to/file.cpp' -> 'file'
        file_name = os.path.splitext(os.path.basename(source_file))[0]
        if _is_cuda_file(source_file) and with_cuda:
            # Use a different object filename in case a C++ and CUDA file have
            # the same filename but different extension (.cpp vs. .cu).
            target = f'{file_name}.cuda.o'
        elif _is_sycl_file(source_file) and with_sycl:
            target = f'{file_name}.sycl.o'
        else:
            target = f'{file_name}.o'
        return target

    objects = [object_file_path(src) for src in sources]
    ldflags = ([] if is_standalone else [SHARED_FLAG]) + extra_ldflags

    # The darwin linker needs explicit consent to ignore unresolved symbols.
    if IS_MACOS:
        ldflags.append('-undefined dynamic_lookup')
    elif IS_WINDOWS:
        ldflags = _nt_quote_args(ldflags)

    ext = EXEC_EXT if is_standalone else LIB_EXT
    library_target = f'{name}{ext}'

    _write_ninja_file(
        path=path,
        cflags=cflags,
        post_cflags=None,
        cuda_cflags=cuda_flags,
        cuda_post_cflags=None,
        cuda_dlink_post_cflags=None,
        sycl_cflags=sycl_cflags,
        sycl_post_cflags=[],
        sycl_dlink_post_cflags=sycl_dlink_post_cflags,
        sources=sources,
        objects=objects,
        ldflags=ldflags,
        library_target=library_target,
        with_cuda=with_cuda,
        with_sycl=with_sycl)