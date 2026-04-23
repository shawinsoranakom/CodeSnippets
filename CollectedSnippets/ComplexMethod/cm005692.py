def is_torch_tf32_available() -> bool:
    if not is_torch_available():
        return False

    import torch

    if is_torch_musa_available() and hasattr(torch, "musa"):
        device_info = torch.musa.get_device_properties(torch.musa.current_device())
        if f"{device_info.major}{device_info.minor}" >= "22":
            return True
        return False
    torch_version = getattr(torch, "version")
    if not torch.cuda.is_available() or torch_version.cuda is None:
        return False
    if torch.cuda.get_device_properties(torch.cuda.current_device()).major < 8:
        return False
    return True