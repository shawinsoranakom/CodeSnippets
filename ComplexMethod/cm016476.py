def should_use_fp16(device=None, model_params=0, prioritize_performance=True, manual_cast=False):
    if device is not None:
        if is_device_cpu(device):
            return False

    if args.force_fp16:
        return True

    if FORCE_FP32:
        return False

    if is_directml_enabled():
        return True

    if (device is not None and is_device_mps(device)) or mps_mode():
        return True

    if cpu_mode():
        return False

    if is_intel_xpu():
        if torch_version_numeric < (2, 3):
            return True
        else:
            return torch.xpu.get_device_properties(device).has_fp16

    if is_ascend_npu():
        return True

    if is_mlu():
        return True

    if is_ixuca():
        return True

    if torch.version.hip:
        return True

    props = torch.cuda.get_device_properties(device)
    if props.major >= 8:
        return True

    if props.major < 6:
        return False

    #FP16 is confirmed working on a 1080 (GP104) and on latest pytorch actually seems faster than fp32
    nvidia_10_series = ["1080", "1070", "titan x", "p3000", "p3200", "p4000", "p4200", "p5000", "p5200", "p6000", "1060", "1050", "p40", "p100", "p6", "p4"]
    for x in nvidia_10_series:
        if x in props.name.lower():
            if WINDOWS or manual_cast:
                return True
            else:
                return False #weird linux behavior where fp32 is faster

    if manual_cast:
        free_model_memory = maximum_vram_for_weights(device)
        if (not prioritize_performance) or model_params * 4 > free_model_memory:
            return True

    if props.major < 7:
        return False

    #FP16 is just broken on these cards
    nvidia_16_series = ["1660", "1650", "1630", "T500", "T550", "T600", "MX550", "MX450", "CMP 30HX", "T2000", "T1000", "T1200"]
    for x in nvidia_16_series:
        if x in props.name:
            return False

    return True