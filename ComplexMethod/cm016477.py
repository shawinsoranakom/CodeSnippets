def should_use_bf16(device=None, model_params=0, prioritize_performance=True, manual_cast=False):
    if device is not None:
        if is_device_cpu(device): #TODO ? bf16 works on CPU but is extremely slow
            return False

    if FORCE_FP32:
        return False

    if directml_enabled:
        return False

    if (device is not None and is_device_mps(device)) or mps_mode():
        if mac_version() < (14,):
            return False
        return True

    if cpu_mode():
        return False

    if is_intel_xpu():
        if torch_version_numeric < (2, 3):
            return True
        else:
            return torch.xpu.is_bf16_supported()

    if is_ascend_npu():
        return True

    if is_ixuca():
        return True

    if is_amd():
        arch = torch.cuda.get_device_properties(device).gcnArchName
        if any((a in arch) for a in AMD_RDNA2_AND_OLDER_ARCH):  # RDNA2 and older don't support bf16
            if manual_cast:
                return True
            return False

    props = torch.cuda.get_device_properties(device)

    if is_mlu():
        if props.major > 3:
            return True

    if props.major >= 8:
        return True

    bf16_works = torch.cuda.is_bf16_supported()

    if bf16_works and manual_cast:
        free_model_memory = maximum_vram_for_weights(device)
        if (not prioritize_performance) or model_params * 4 > free_model_memory:
            return True

    return False