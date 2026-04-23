def get_vram(device) -> int:
    env_vram = os.getenv("MINERU_VIRTUAL_VRAM_SIZE")

    # 如果环境变量已配置,尝试解析并返回
    if env_vram is not None:
        try:
            total_memory = int(env_vram)
            if total_memory > 0:
                return total_memory
            else:
                logger.warning(
                    f"MINERU_VIRTUAL_VRAM_SIZE value '{env_vram}' is not positive, falling back to auto-detection")
        except ValueError:
            logger.warning(
                f"MINERU_VIRTUAL_VRAM_SIZE value '{env_vram}' is not a valid integer, falling back to auto-detection")

    # 环境变量未配置或配置错误,根据device自动获取
    total_memory = 1
    if torch.cuda.is_available() and str(device).startswith("cuda"):
        total_memory = round(torch.cuda.get_device_properties(device).total_memory / (1024 ** 3))  # 将字节转换为 GB
    elif str(device).startswith("npu"):
        if torch_npu.npu.is_available():
            total_memory = round(torch_npu.npu.get_device_properties(device).total_memory / (1024 ** 3))  # 转为 GB
    elif str(device).startswith("gcu"):
        if torch.gcu.is_available():
            total_memory = round(torch.gcu.get_device_properties(device).total_memory / (1024 ** 3))  # 转为 GB
    elif str(device).startswith("musa"):
        if torch.musa.is_available():
            total_memory = round(torch.musa.get_device_properties(device).total_memory / (1024 ** 3))  # 转为 GB
    elif str(device).startswith("mlu"):
        if torch.mlu.is_available():
            total_memory = round(torch.mlu.get_device_properties(device).total_memory / (1024 ** 3))  # 转为 GB
    elif str(device).startswith("sdaa"):
        if torch.sdaa.is_available():
            total_memory = round(torch.sdaa.get_device_properties(device).total_memory / (1024 ** 3))  # 转为 GB          

    return total_memory