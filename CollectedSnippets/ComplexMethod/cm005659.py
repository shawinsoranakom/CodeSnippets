def device_validator(value: str | int | None = None):
    possible_names = ["cpu", "cuda", "xla", "xpu", "mps", "meta"]
    if value is None:
        pass
    elif is_torch_available() and isinstance(value, torch.device):
        # Convert torch.device to string for validation
        device_str = str(value)
        if device_str.split(":")[0] not in possible_names:
            raise ValueError(
                f"If device is a torch.device, the value must be one of {possible_names} but got device={value}"
            )
    elif isinstance(value, int) and value < 0:
        raise ValueError(
            f"If device is an integer, the value must be a strictly positive integer but got device={value}"
        )
    elif isinstance(value, str) and value.split(":")[0] not in possible_names:
        raise ValueError(f"If device is an string, the value must be one of {possible_names} but got device={value}")
    elif not isinstance(value, (int, str)):
        raise ValueError(
            f"Device must be either an integer device ID, a string (e.g., 'cpu', 'cuda:0'), or a torch.device object, but got device={value}"
        )