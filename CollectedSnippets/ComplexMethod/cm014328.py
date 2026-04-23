def _prepare_ldflags(extra_ldflags, with_cuda, with_sycl, verbose, is_standalone):
    if IS_WINDOWS:
        python_lib_path = os.path.join(sys.base_exec_prefix, 'libs')

        extra_ldflags.append('c10.lib')
        if with_cuda:
            extra_ldflags.append('c10_hip.lib' if IS_HIP_EXTENSION else 'c10_cuda.lib')
        if with_sycl:
            extra_ldflags.append('c10_xpu.lib')
        extra_ldflags.append('torch_cpu.lib')
        if with_cuda:
            extra_ldflags.append('torch_hip.lib' if IS_HIP_EXTENSION else 'torch_cuda.lib')
            # /INCLUDE is used to ensure torch_cuda is linked against in a project that relies on it.
            # Related issue: https://github.com/pytorch/pytorch/issues/31611
            extra_ldflags.append('-INCLUDE:?warp_size@cuda@at@@YAHXZ')
        if with_sycl:
            extra_ldflags.append('torch_xpu.lib')
        extra_ldflags.append('torch.lib')
        extra_ldflags.append(f'/LIBPATH:{TORCH_LIB_PATH}')
        if not is_standalone:
            extra_ldflags.append('torch_python.lib')
            extra_ldflags.append(f'/LIBPATH:{python_lib_path}')

    else:
        extra_ldflags.append(f'-L{TORCH_LIB_PATH}')
        extra_ldflags.append('-lc10')
        if with_cuda:
            extra_ldflags.append('-lc10_hip' if IS_HIP_EXTENSION else '-lc10_cuda')
        if with_sycl:
            extra_ldflags.append('-lc10_xpu')
        extra_ldflags.append('-ltorch_cpu')
        if with_cuda:
            extra_ldflags.append('-ltorch_hip' if IS_HIP_EXTENSION else '-ltorch_cuda')
        if with_sycl:
            extra_ldflags.append('-ltorch_xpu')
        extra_ldflags.append('-ltorch')
        if not is_standalone:
            extra_ldflags.append('-ltorch_python')

        if is_standalone:
            extra_ldflags.append(f"-Wl,-rpath,{TORCH_LIB_PATH}")

    if with_cuda:
        if verbose:
            logger.info('Detected CUDA files, patching ldflags')
        if IS_WINDOWS and not IS_HIP_EXTENSION:
            extra_ldflags.append(f'/LIBPATH:{_join_cuda_home("lib", "x64")}')
            extra_ldflags.append('cudart.lib')
            if CUDNN_HOME is not None:
                extra_ldflags.append(f'/LIBPATH:{os.path.join(CUDNN_HOME, "lib", "x64")}')
        elif not IS_HIP_EXTENSION:
            extra_lib_dir = "lib64"
            if (not os.path.exists(_join_cuda_home(extra_lib_dir)) and
                    os.path.exists(_join_cuda_home("lib"))):
                # 64-bit CUDA may be installed in "lib"
                # Note that it's also possible both don't exist (see _find_cuda_home) - in that case we stay with "lib64"
                extra_lib_dir = "lib"
            extra_ldflags.append(f'-L{_join_cuda_home(extra_lib_dir)}')
            extra_ldflags.append('-lcudart')
            if CUDNN_HOME is not None:
                extra_ldflags.append(f'-L{os.path.join(CUDNN_HOME, "lib64")}')
        elif IS_HIP_EXTENSION:
            if IS_WINDOWS:
                extra_ldflags.append(f'/LIBPATH:{_join_rocm_home("lib")}')
                extra_ldflags.append('amdhip64.lib')
            else:
                extra_ldflags.append(f'-L{_join_rocm_home("lib")}')
                extra_ldflags.append('-lamdhip64')
    if with_sycl:
        if IS_WINDOWS:
            extra_ldflags.append(f'/LIBPATH:{_join_sycl_home("lib")}')
            extra_ldflags.append('sycl.lib')
        else:
            extra_ldflags.append(f'-L{_join_sycl_home("lib")}')
            extra_ldflags.append('-lsycl')
    return extra_ldflags