def _get_rocm_arch_flags(cflags: list[str] | None = None) -> list[str]:
    # If cflags is given, there may already be user-provided arch flags in it
    # (from `extra_compile_args`). If user also specified -fgpu-rdc or -fno-gpu-rdc, we
    # assume they know what they're doing. Otherwise, we force -fno-gpu-rdc default.
    has_gpu_rdc_flag = False
    if cflags is not None:
        has_custom_flags = False
        for flag in cflags:
            if 'amdgpu-target' in flag or 'offload-arch' in flag:
                has_custom_flags = True
            elif 'gpu-rdc' in flag:
                has_gpu_rdc_flag = True
        if has_custom_flags:
            return [] if has_gpu_rdc_flag else ['-fno-gpu-rdc']
    # Use same defaults as used for building PyTorch
    # Allow env var to override, just like during initial cmake build.
    _archs = os.environ.get('PYTORCH_ROCM_ARCH', None)
    if not _archs:
        arch_set = set()
        # the assumption is that the extension should run on any of the currently visible cards,
        # which could be of different types - therefore all archs for visible cards should be included
        for i in range(torch.cuda.device_count()):
            device_properties = torch.cuda.get_device_properties(i)
            if hasattr(device_properties, "gcnArchName"):
                device_arch = (device_properties.gcnArchName).split(":", 1)[0]
                arch_set.add(device_arch)

        archs = ";".join(arch_set)

        logger.warning(
            "The environment variable `PYTORCH_ROCM_ARCH` is not set, all archs for visible cards are included for compilation (%s).\n"
            "If this is not desired, please set the environment variable `PYTORCH_ROCM_ARCH` to specific architectures.", archs)
    else:
        archs = _archs.replace(' ', ';')

    archs = archs.split(';')
    flags = [f'--offload-arch={arch}' for arch in archs]
    flags += [] if has_gpu_rdc_flag else ['-fno-gpu-rdc']
    return flags