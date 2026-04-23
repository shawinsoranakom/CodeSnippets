def get_device_dtype_sm(idx: int) -> tuple[torch.device, torch.dtype, float, float]:
    cpu = torch.device("cpu")
    cuda = torch.device(f"cuda:{idx}")
    if not torch.cuda.is_available():
        return cpu, torch.float32, 0.0, 0.0
    device_idx = idx
    capability = torch.cuda.get_device_capability(device_idx)
    name = torch.cuda.get_device_name(device_idx)
    mem_bytes = torch.cuda.get_device_properties(device_idx).total_memory
    mem_gb = mem_bytes / (1024**3) + 0.4
    major, minor = capability
    sm_version = major + minor / 10.0
    is_16_series = bool(re.search(r"16\d{2}", name)) and sm_version == 7.5
    if mem_gb < 4 or sm_version < 5.3:
        return cpu, torch.float32, 0.0, 0.0
    if sm_version == 6.1 or is_16_series == True:
        return cuda, torch.float32, sm_version, mem_gb
    if sm_version > 6.1:
        return cuda, torch.float16, sm_version, mem_gb
    return cpu, torch.float32, 0.0, 0.0