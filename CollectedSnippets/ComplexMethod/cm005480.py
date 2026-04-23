def check_and_set_device_map(device_map: "torch.device | int | str | dict | None") -> dict | str | None:
    from ..modeling_utils import get_torch_context_manager_or_global_device

    # Potentially detect context manager or global device, and use it (only if no device_map was provided)
    if device_map is None and not is_deepspeed_zero3_enabled():
        device_in_context = get_torch_context_manager_or_global_device()
        if device_in_context == torch.device("meta"):
            raise RuntimeError(
                "You are using `from_pretrained` with a meta device context manager or `torch.set_default_device('meta')`.\n"
                "This is an anti-pattern as `from_pretrained` wants to load existing weights.\nIf you want to initialize an "
                "empty model on the meta device, use the context manager or global device with `from_config`, or `ModelClass(config)`"
            )
        device_map = device_in_context

    # change device_map into a map if we passed an int, a str or a torch.device
    if isinstance(device_map, torch.device):
        device_map = {"": device_map}
    elif isinstance(device_map, str) and device_map not in ["auto", "balanced", "balanced_low_0", "sequential"]:
        try:
            if device_map == "cuda":
                # setting to the local rank
                local_rank = int(os.environ.get("LOCAL_RANK", 0))
                device_map = f"cuda:{local_rank}"
            device_map = {"": torch.device(device_map)}
        except RuntimeError:
            raise ValueError(
                "When passing device_map as a string, the value needs to be a device name (e.g. cpu, cuda:0) or "
                f"'auto', 'balanced', 'balanced_low_0', 'sequential' but found {device_map}."
            )
    elif isinstance(device_map, int):
        if device_map < 0:
            raise ValueError(
                "You can't pass device_map as a negative int. If you want to put the model on the cpu, pass device_map = 'cpu' "
            )
        else:
            device_map = {"": device_map}

    if device_map is not None:
        if is_deepspeed_zero3_enabled():
            raise ValueError("DeepSpeed Zero-3 is not compatible with passing a `device_map`.")
        if not is_accelerate_available():
            raise ValueError(
                "Using a `device_map`, `tp_plan`, `torch.device` context manager or setting `torch.set_default_device(device)` "
                "requires `accelerate`. You can install it with `pip install accelerate`"
            )
    return device_map