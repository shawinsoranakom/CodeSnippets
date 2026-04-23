def enable_custom_logits_processors() -> bool:
    import torch
    from vllm import __version__ as vllm_version

    if torch.cuda.is_available():
        major, minor = torch.cuda.get_device_capability()
        # 正确计算Compute Capability
        compute_capability = f"{major}.{minor}"
    elif hasattr(torch, 'npu') and torch.npu.is_available():
        compute_capability = "8.0"
    elif hasattr(torch, 'gcu') and torch.gcu.is_available():
        compute_capability = "8.0"
    elif hasattr(torch, 'musa') and torch.musa.is_available():
        compute_capability = "8.0"
    elif hasattr(torch, 'mlu') and torch.mlu.is_available():
        compute_capability = "8.0"
    elif hasattr(torch, 'sdaa') and torch.sdaa.is_available():
        compute_capability = "8.0"

    else:
        logger.info("CUDA not available, disabling custom_logits_processors")
        return False

    # 安全地处理环境变量
    vllm_use_v1_str = os.getenv('VLLM_USE_V1', "1")
    if vllm_use_v1_str.isdigit():
        vllm_use_v1 = int(vllm_use_v1_str)
    else:
        vllm_use_v1 = 1

    if vllm_use_v1 == 0:
        logger.info("VLLM_USE_V1 is set to 0, disabling custom_logits_processors")
        return False
    elif version.parse(vllm_version) < version.parse("0.10.1"):
        logger.info(f"vllm version: {vllm_version} < 0.10.1, disable custom_logits_processors")
        return False
    elif version.parse(compute_capability) < version.parse("8.0"):
        if version.parse(vllm_version) >= version.parse("0.10.2"):
            logger.info(f"compute_capability: {compute_capability} < 8.0, but vllm version: {vllm_version} >= 0.10.2, enable custom_logits_processors")
            return True
        else:
            logger.info(f"compute_capability: {compute_capability} < 8.0 and vllm version: {vllm_version} < 0.10.2, disable custom_logits_processors")
            return False
    else:
        logger.info(f"compute_capability: {compute_capability} >= 8.0 and vllm version: {vllm_version} >= 0.10.1, enable custom_logits_processors")
        return True