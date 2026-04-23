def get_available_devices() -> frozenset[str]:
    """
    Returns a frozenset of devices available for the current PyTorch installation.
    """
    devices = {"cpu"}  # `cpu` is always supported as a device in PyTorch

    if is_torch_cuda_available():
        devices.add("cuda")

    if is_torch_mps_available():
        devices.add("mps")

    if is_torch_xpu_available():
        devices.add("xpu")

    if is_torch_npu_available():
        devices.add("npu")

    if is_torch_hpu_available():
        devices.add("hpu")

    if is_torch_mlu_available():
        devices.add("mlu")

    if is_torch_musa_available():
        devices.add("musa")

    return frozenset(devices)