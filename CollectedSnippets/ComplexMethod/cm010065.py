def _get_device_attr(get_member):
    device_type = _get_available_device_type()
    if device_type and device_type.lower() == "cuda":
        return get_member(torch.cuda)
    if device_type and device_type.lower() == "mps":
        return get_member(torch.mps)
    if device_type and device_type.lower() == "xpu":
        return get_member(torch.xpu)  # type: ignore[attr-defined]
    if device_type and device_type.lower() == "mtia":
        return get_member(torch.mtia)
    if device_type == torch._C._get_privateuse1_backend_name():
        return get_member(getattr(torch, device_type))
    # add more available device types here
    return None