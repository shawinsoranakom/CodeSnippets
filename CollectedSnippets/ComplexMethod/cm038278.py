def register_linear_kernel(
    kernel_class: type,
    platform: PlatformEnum,
    kernel_type: str = "mp",
) -> None:
    """
    Register a new linear kernel class to be considered in kernel selection.

    Args:
        kernel_class (type): The kernel class to register.
        platform (PlatformEnum): The platform for which this kernel is applicable.
        kernel_type (str): The type of the kernel, either "mp", "int8", or "fp8".
            Defaults to "mp".

    Raises:
        ValueError: If the kernel_type is not recognized.
    """
    if kernel_type == "mp":
        if platform not in _POSSIBLE_KERNELS:
            _POSSIBLE_KERNELS[platform] = []
        _POSSIBLE_KERNELS[platform].append(kernel_class)
    elif kernel_type == "int8":
        if platform not in _POSSIBLE_INT8_KERNELS:
            _POSSIBLE_INT8_KERNELS[platform] = []
        _POSSIBLE_INT8_KERNELS[platform].append(kernel_class)
    elif kernel_type == "fp8":
        if platform not in _POSSIBLE_FP8_KERNELS:
            _POSSIBLE_FP8_KERNELS[platform] = []
        _POSSIBLE_FP8_KERNELS[platform].append(kernel_class)
    elif kernel_type == "mxfp8":
        if platform not in _POSSIBLE_MXFP8_KERNELS:
            _POSSIBLE_MXFP8_KERNELS[platform] = []
        _POSSIBLE_MXFP8_KERNELS[platform].append(kernel_class)
    elif kernel_type == "nvfp4":
        if platform not in _POSSIBLE_NVFP4_KERNELS:
            _POSSIBLE_NVFP4_KERNELS[platform] = []
        _POSSIBLE_NVFP4_KERNELS[platform].append(kernel_class)
    else:
        raise ValueError(f"Unrecognized kernel type: {kernel_type}")