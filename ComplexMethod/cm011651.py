def is_big_gpu(index_or_device: int | torch.device = 0) -> bool:
    if isinstance(index_or_device, torch.device):
        device = index_or_device
    else:
        device = torch.device(get_gpu_type(), index_or_device)

    prop = DeviceProperties.create(device)

    # SM logic is not relevant to ROCm gpus
    # Arbitrarily skipping the older models
    if torch.version.hip:
        assert prop.major is not None
        if prop.major < 9 or prop.major == 10:
            log.warning("GPU arch does not support max_autotune_gemm mode usage")
            return False
        return True

    min_sms = 16 if device.type == "xpu" else 68  # 3080
    avail_sms = prop.multi_processor_count
    if avail_sms < min_sms:
        log.warning(
            "Not enough SMs to use max_autotune_gemm mode",
            extra={"min_sms": min_sms, "avail_sms": avail_sms},
        )
        return False
    return True