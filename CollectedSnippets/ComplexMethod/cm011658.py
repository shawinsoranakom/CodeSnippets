def use_ck_template(layout: Layout) -> bool:
    # config knobs check 1
    if not (config.max_autotune or config.max_autotune_gemm):
        return False
    # platform check
    if not torch.version.hip:
        return False
    # tensors must be on GPU
    if layout.device.type != "cuda":
        return False
    # hardware check
    # if config arch list is not specified, get the native arch from the device properties
    native_arch = _rocm_native_device_arch_name(layout.device)
    requested_archs = {k.split(":")[0]: k for k in config.rocm.arch} or {
        native_arch.split(":")[0]: native_arch
    }
    requested_supported_archs = [
        requested_archs[k]
        for k in requested_archs.keys() & config.rocm.ck_supported_arch
    ]
    if not requested_supported_archs:
        return False
    # supported input dtypes
    if layout.dtype not in [torch.float16, torch.bfloat16, torch.float32]:
        return False

    ck_package_dirname, _, _, _ = try_import_ck_lib()

    if not ck_package_dirname:
        log.warning("Please pip install Composable Kernel package")
        return False

    config.rocm.ck_dir = ck_package_dirname

    return True