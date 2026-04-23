def get_device(args, kwargs):
    if kwargs.get("device"):
        device = kwargs.get("device")
        if isinstance(device, str):
            device = torch.device(device)
        return device.type

    devices = {arg.device.type for arg in args if isinstance(arg, torch.Tensor)}
    if any(dev == "cuda" for dev in devices):
        return "cuda"
    elif any(dev == "xpu" for dev in devices):
        return "xpu"
    elif any(dev == "hpu" for dev in devices):
        return "hpu"
    elif any(dev == "cpu" for dev in devices):
        return "cpu"
    return None