def include_paths(device_type: str = "cpu", torch_include_dirs=True) -> list[str]:
    """
    Get the include paths required to build a C++ or CUDA or SYCL extension.

    Args:
        device_type: Defaults to "cpu".
    Returns:
        A list of include path strings.
    """
    paths = []
    lib_include = os.path.join(_TORCH_PATH, 'include')
    if torch_include_dirs:
        paths.extend([
            lib_include,
            # Remove this once torch/torch.h is officially no longer supported for C++ extensions.
            os.path.join(lib_include, 'torch', 'csrc', 'api', 'include'),
        ])
    if device_type == "cuda" and IS_HIP_EXTENSION:
        paths.append(os.path.join(lib_include, 'THH'))
        paths.append(_join_rocm_home('include'))
    elif device_type == "cuda":
        cuda_home_include = _join_cuda_home('include')
        # if we have the Debian/Ubuntu packages for cuda, we get /usr as cuda home.
        # but gcc doesn't like having /usr/include passed explicitly
        if cuda_home_include != '/usr/include':
            paths.append(cuda_home_include)

        # Support CUDA_INC_PATH env variable supported by CMake files
        if (cuda_inc_path := os.environ.get("CUDA_INC_PATH", None)) and \
                cuda_inc_path != '/usr/include':

            paths.append(cuda_inc_path)
        if CUDNN_HOME is not None:
            paths.append(os.path.join(CUDNN_HOME, 'include'))
    elif device_type == "xpu":
        paths.append(_join_sycl_home('include'))
        paths.append(_join_sycl_home('include', 'sycl'))
    return paths