def smoke_test_cuda(
    package: str,
    runtime_error_check: str,
    torch_compile_check: str,
    pypi_pkg_check: str,
) -> None:
    if not torch.cuda.is_available() and is_cuda_system:
        raise RuntimeError(f"Expected CUDA {gpu_arch_ver}. However CUDA is not loaded.")

    if package in ["all", "torch_torchvision"] and is_cuda_system:
        for module in get_modules_for_package(package):
            imported_module = importlib.import_module(module["name"])
            # TBD for vision move extension module to private so it will
            # be _extention.
            version = "N/A"
            if module["extension"] == "extension":
                version = imported_module.extension._check_cuda_version()
            else:
                version = imported_module._extension._check_cuda_version()
            print(f"{module['name']} CUDA: {version}")

    if torch_compile_check == "enabled" and target_os in [
        "linux",
        "linux-aarch64",
        "macos-arm64",
        "darwin",
    ]:
        smoke_test_compile("cuda" if torch.cuda.is_available() else "cpu")

    if torch.cuda.is_available():
        if torch.version.cuda != gpu_arch_ver:
            raise RuntimeError(
                f"Wrong CUDA version. Loaded: {torch.version.cuda} Expected: {gpu_arch_ver}"
            )

        print(f"torch cuda: {torch.version.cuda}")
        torch.cuda.init()
        print("CUDA initialized successfully")
        print(f"Number of CUDA devices: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"Device {i}: {torch.cuda.get_device_name(i)}")

        print(f"cuDNN enabled? {torch.backends.cudnn.enabled}")
        torch_cudnn_version = cudnn_to_version_str(torch.backends.cudnn.version())
        print(f"Torch cuDNN version: {torch_cudnn_version}")

        torch_cudnn_compile_version = torch._C._cudnn.getCompileVersion()
        print(f"Torch cuDNN compile-time version: {torch_cudnn_compile_version}")
        torch_cudnn_runtime_version = tuple(
            [int(x) for x in torch_cudnn_version.split(".")]
        )
        if torch_cudnn_runtime_version != torch_cudnn_compile_version:
            raise RuntimeError(
                "cuDNN runtime version doesn't match comple version. "
                f"Loaded: {torch_cudnn_runtime_version} "
                f"Expected: {torch_cudnn_compile_version}"
            )

        check_cudnn_version(gpu_arch_ver, torch_cudnn_version)

        if sys.platform in ["linux", "linux2"]:
            torch_nccl_version = ".".join(str(v) for v in torch.cuda.nccl.version())
            print(f"Torch nccl; version: {torch_nccl_version}")

        # Pypi dependencies are installed on linux only and nccl is available only on Linux.
        if pypi_pkg_check == "enabled" and sys.platform in ["linux", "linux2"]:
            compare_pypi_to_torch_versions(
                "cudnn", find_pypi_package_version("nvidia-cudnn"), torch_cudnn_version
            )
            compare_pypi_to_torch_versions(
                "nccl", find_pypi_package_version("nvidia-nccl"), torch_nccl_version
            )

        if runtime_error_check == "enabled":
            test_cuda_runtime_errors_captured()