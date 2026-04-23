def get_cpp_torch_device_options(
    device_type: str,
    aot_mode: bool = False,
    compile_only: bool = False,
) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str], list[str]]:
    """
    This function is used to get the build args of device related build options.
    1. Device include_directories, libraries, libraries_directories.
    2. Device MACROs.
    3. MISC
    4. Return the build args
    """
    definitions: list[str] = []
    include_dirs: list[str] = []
    cflags: list[str] = []
    ldflags: list[str] = []
    libraries_dirs: list[str] = []
    libraries: list[str] = []
    passthrough_args: list[str] = []
    if (
        config.is_fbcode()
        and "CUDA_HOME" not in os.environ
        and "CUDA_PATH" not in os.environ
    ):
        os.environ["CUDA_HOME"] = build_paths.sdk_home

    _set_gpu_runtime_env()
    from torch.utils import cpp_extension

    include_dirs = cpp_extension.include_paths(
        device_type, config.aot_inductor.link_libtorch is None
    )
    link_libtorch = config.aot_inductor.link_libtorch
    libraries_dirs = cpp_extension.library_paths(
        device_type,
        torch_include_dirs=link_libtorch,
        cross_target_platform=config.aot_inductor.cross_target_platform,
    )
    if device_type == "cuda":
        definitions.append(" USE_ROCM" if torch.version.hip else " USE_CUDA")

        if torch.version.hip is not None:
            if config.is_fbcode() or not link_libtorch:
                libraries += ["amdhip64"]
            else:
                libraries += ["torch_hip"]
            definitions.append(" __HIP_PLATFORM_AMD__")
        else:
            if config.is_fbcode() or not link_libtorch:
                libraries += ["cuda"]
            else:
                libraries += ["cuda", "torch_cuda"]
            if config.aot_inductor.cross_target_platform == "windows":
                extra_libs = _ensure_mingw_cudart_import_lib(libraries_dirs)
                libraries += ["cudart"] + extra_libs
            _transform_cuda_paths(libraries_dirs)

    if device_type == "xpu":
        definitions.append(" USE_XPU")
        xpu_error_string = (
            "Intel GPU driver is not properly installed, please follow the instruction "
            "in https://github.com/pytorch/pytorch?tab=readme-ov-file#intel-gpu-support."
        )
        if _IS_WINDOWS:
            ze_root = os.getenv("LEVEL_ZERO_V1_SDK_PATH")
            if ze_root is None:
                raise OSError(xpu_error_string)
            include_dirs += [os.path.join(ze_root, "include")]
            libraries_dirs += [os.path.join(ze_root, "lib")]
        else:
            # Suppress multi-line comment warnings in sycl headers
            cflags += ["Wno-comment"]
            if not find_library("ze_loader"):
                raise OSError(xpu_error_string)

        libraries += ["ze_loader", "sycl"]
        if link_libtorch:
            libraries += ["torch_xpu"]

    if device_type == "mps":
        definitions.append(" USE_MPS")

    if config.is_fbcode():
        include_dirs.append(build_paths.sdk_include)

        if aot_mode and device_type == "cuda":
            if torch.version.hip is None:
                if not compile_only:
                    # Only add link args, when compile_only is false.
                    passthrough_args = ["-Wl,-Bstatic -lcudart_static -Wl,-Bdynamic"]

        if device_type == "cpu":
            (
                stdcxx_lib_dir_paths,
                stdcxx_libs,
            ) = _get_libstdcxx_args()
            libraries_dirs += stdcxx_lib_dir_paths
            libraries += stdcxx_libs

    if config.aot_inductor.custom_op_libs:
        libraries += config.aot_inductor.custom_op_libs

    return (
        definitions,
        include_dirs,
        cflags,
        ldflags,
        libraries_dirs,
        libraries,
        passthrough_args,
    )