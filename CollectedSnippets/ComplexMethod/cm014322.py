def library_paths(device_type: str = "cpu", torch_include_dirs: bool = True, cross_target_platform: str | None = None) -> list[str]:
    """
    Get the library paths required to build a C++ or CUDA extension.

    Args:
        device_type: Defaults to "cpu".

    Returns:
        A list of library path strings.
    """

    paths = []

    if torch_include_dirs:
        # We need to link against libtorch.so
        paths.extend([TORCH_LIB_PATH])

    if device_type == "cuda" and IS_HIP_EXTENSION:
        lib_dir = 'lib'
        paths.append(_join_rocm_home(lib_dir))
        if HIP_HOME is not None:
            paths.append(os.path.join(HIP_HOME, 'lib'))
    elif device_type == "cuda":
        if cross_target_platform == "windows":
            lib_dir = os.path.join('lib', 'x64')
            if WINDOWS_CUDA_HOME is None:
                raise RuntimeError("Need to set WINDOWS_CUDA_HOME for windows cross-compilation")
            paths.append(os.path.join(WINDOWS_CUDA_HOME, lib_dir))
        else:
            if IS_WINDOWS:
                lib_dir = os.path.join('lib', 'x64')
            else:
                lib_dir = 'lib64'
                if (not os.path.exists(_join_cuda_home(lib_dir)) and
                        os.path.exists(_join_cuda_home('lib'))):
                    # 64-bit CUDA may be installed in 'lib' (see e.g. gh-16955)
                    # Note that it's also possible both don't exist (see
                    # _find_cuda_home) - in that case we stay with 'lib64'.
                    lib_dir = 'lib'

            paths.append(_join_cuda_home(lib_dir))
            if CUDNN_HOME is not None:
                paths.append(os.path.join(CUDNN_HOME, lib_dir))
    elif device_type == "xpu":
        if IS_WINDOWS:
            lib_dir = os.path.join('lib', 'x64')
        else:
            lib_dir = 'lib64'
            if (not os.path.exists(_join_sycl_home(lib_dir)) and
                    os.path.exists(_join_sycl_home('lib'))):
                lib_dir = 'lib'

        paths.append(_join_sycl_home(lib_dir))

    return paths