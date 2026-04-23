def _check_cubins():
    incompatible_device_warn = """
{} with CUDA capability sm_{} is not compatible with the current PyTorch installation.
The current PyTorch install supports CUDA capabilities {}.
If you want to use the {} GPU with PyTorch, please check the instructions at https://pytorch.org/get-started/locally/
"""
    if torch.version.cuda is None:  # on ROCm we don't want this check
        return
    arch_list = get_arch_list()
    if len(arch_list) == 0:
        return
    supported_sm = [_extract_arch_version(arch) for arch in arch_list if "sm_" in arch]
    for idx in range(device_count()):
        cap_major, cap_minor = get_device_capability(idx)
        # NVIDIA GPU compute architectures are backward compatible within major version
        supported = any(sm // 10 == cap_major for sm in supported_sm)
        if not supported:
            device_name = get_device_name(idx)
            capability = cap_major * 10 + cap_minor
            warnings.warn(
                incompatible_device_warn.format(
                    device_name, capability, " ".join(arch_list), device_name
                ),
                stacklevel=2,
            )