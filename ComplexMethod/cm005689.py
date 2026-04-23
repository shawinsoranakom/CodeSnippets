def is_torch_musa_available(check_device=False) -> bool:
    "Checks if `torch_musa` is installed and potentially if a MUSA is in the environment"
    if not is_torch_available() or not _is_package_available("torch_musa")[0]:
        return False

    import torch
    import torch_musa  # noqa: F401

    torch_musa_min_version = "0.33.0"
    accelerate_available, accelerate_version = _is_package_available("accelerate", return_version=True)
    if accelerate_available and version.parse(accelerate_version) < version.parse(torch_musa_min_version):
        return False

    if check_device:
        try:
            # Will raise a RuntimeError if no MUSA is found
            if hasattr(torch, "musa"):
                _ = torch.musa.device_count()
                return torch.musa.is_available()
            return False
        except RuntimeError:
            return False
    return hasattr(torch, "musa") and torch.musa.is_available()