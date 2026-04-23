def _nvrtc_compile(
    kernel_source: str,
    kernel_name: str,
    compute_capability: str | None = None,
    cuda_include_dirs: list | None = None,
    nvcc_options: list | None = None,
    auto_pch: bool = False,
) -> tuple[bytes, str]:
    """
    Compiles a CUDA kernel using NVRTC and returns the PTX code.

    Args:
        kernel_source (str): The CUDA kernel source code as a string
        kernel_name (str): The name of the kernel function to compile
        compute_capability (str, None): The compute capability to target (e.g., "86").
                                           If None, will detect from current device.
        cuda_include_dirs (list, None): List of directories containing CUDA headers
        nvcc_options (list, None): Additional options to pass to NVRTC
        auto_pch (bool): Enable automatic precompiled headers (CUDA 12.8+)

    Returns:
        Tuple[bytes, str]: The compiled PTX code and mangled kernel name
    """
    # Ensure CUDA is initialized
    import torch.cuda

    # Load NVRTC library
    libnvrtc = _get_gpu_rtc_library()

    # NVRTC constants
    NVRTC_SUCCESS = 0

    # Helper: check NVRTC errors
    def check_nvrtc(result: int) -> None:
        if result != NVRTC_SUCCESS:
            err_str = ctypes.c_char_p()
            libnvrtc.nvrtcGetErrorString(result, ctypes.byref(err_str))
            error_message = (
                err_str.value.decode()
                if err_str.value is not None
                else "Unknown CUDA error"
            )
            raise RuntimeError(f"CUDA error: {error_message}")

    # Convert source to bytes
    source_bytes = kernel_source.encode("utf-8")

    # Get compute capability if not provided
    if compute_capability is None:
        props = torch.cuda.get_device_properties(torch.cuda.current_device())
        if torch.version.hip:
            compute_capability = f"{props.gcnArchName}"
        else:
            compute_capability = f"{props.major}{props.minor}"

    # Prepare compilation options
    options = []
    if torch.version.hip:
        options.append(f"--offload-arch={compute_capability}".encode())
    else:
        options.append(f"--gpu-architecture=sm_{compute_capability}".encode())

    # Auto-detect and add CUDA include paths
    from torch.utils.cpp_extension import include_paths

    cuda_include_paths = include_paths("cuda")
    for cuda_path in cuda_include_paths:
        options.append(f"-I{cuda_path}".encode())

    # Add custom include directories
    if cuda_include_dirs:
        for directory in cuda_include_dirs:
            options.append(f"-I{directory}".encode())

    # Enable automatic precompiled headers (CUDA 12.8+)
    if auto_pch:
        if str(torch.version.cuda) < "12.8":
            raise AssertionError(f"PCH requires CUDA 12.8+, got {torch.version.cuda}")
        if nvcc_options is None:
            nvcc_options = []
        nvcc_options.append("--pch")

    # Add custom NVCC options
    if nvcc_options:
        for option in nvcc_options:
            options.append(option.encode("utf-8"))

    nvrtc_compatible_flags = _get_gpu_rtc_compatible_flags()
    options.extend([flag.encode("utf-8") for flag in nvrtc_compatible_flags])

    # Convert options to C array
    num_options = len(options)
    options_array = (ctypes.c_char_p * num_options)(*options)

    # Create program
    prog = ctypes.c_void_p()
    check_nvrtc(
        libnvrtc.nvrtcCreateProgram(
            ctypes.byref(prog),
            source_bytes,
            f"{kernel_name}.cu".encode(),
            0,
            None,
            None,
        )
    )

    # Add kernel name, which can be a template expression
    c_kernel_name = kernel_name.encode("utf-8")
    check_nvrtc(libnvrtc.nvrtcAddNameExpression(prog, c_kernel_name))

    # Compile program
    res = libnvrtc.nvrtcCompileProgram(prog, num_options, options_array)

    # Handle compilation errors
    if res != NVRTC_SUCCESS:
        # Get log
        log_size = ctypes.c_size_t()
        libnvrtc.nvrtcGetProgramLogSize(prog, ctypes.byref(log_size))
        log = ctypes.create_string_buffer(log_size.value)
        libnvrtc.nvrtcGetProgramLog(prog, log)
        raise RuntimeError(f"Kernel compilation failed:\n{log.value.decode()}")

    # Get binary
    binary_size = ctypes.c_size_t()
    check_nvrtc(libnvrtc.nvrtcGetCUBINSize(prog, ctypes.byref(binary_size)))
    binary = ctypes.create_string_buffer(binary_size.value)
    check_nvrtc(libnvrtc.nvrtcGetCUBIN(prog, binary))

    # Get mangled name
    c_mangled_name = ctypes.c_char_p()
    check_nvrtc(
        libnvrtc.nvrtcGetLoweredName(prog, c_kernel_name, ctypes.byref(c_mangled_name))
    )
    if c_mangled_name.value is not None:
        mangled_name = c_mangled_name.value.decode()  # make a copy
    else:
        mangled_name = ""

    libnvrtc.nvrtcDestroyProgram(ctypes.byref(prog))

    # For some reason, ".value" causes the string to be truncated,
    # likely due to the presence of '\0' in the string. So we use .raw instead.
    return binary.raw, mangled_name