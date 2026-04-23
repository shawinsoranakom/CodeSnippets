def supports_cast(device, dtype): #TODO
    if dtype == torch.float32:
        return True
    if dtype == torch.float16:
        return True
    if directml_enabled: #TODO: test this
        return False
    if dtype == torch.bfloat16:
        return True
    if is_device_mps(device):
        return False
    if dtype == torch.float8_e4m3fn:
        return True
    if dtype == torch.float8_e5m2:
        return True
    return False