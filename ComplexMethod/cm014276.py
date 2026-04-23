def _parse_to_polyfill(
    *args: Any, **kwargs: Any
) -> tuple[torch.device, torch.dtype, bool, torch.memory_format]:
    """
    Polyfill for torch._C._nn._parse_to that parses arguments to nn.Module.to().

    Signature mirrors torch._C._nn._parse_to which accepts:
    - to(device) - device as string or torch.device
    - to(dtype) - dtype as torch.dtype
    - to(tensor) - extracts device and dtype from tensor
    - to(device=..., dtype=..., non_blocking=..., memory_format=...)

    Returns:
        tuple: (device, dtype, non_blocking, memory_format)
    """
    # Check for __torch_function__ mode and dispatch using handle_torch_function pattern
    if _is_torch_function_mode_enabled():
        with _pop_mode_temporarily() as mode:
            result = mode.__torch_function__(
                torch._C._nn._parse_to, tuple(), args, kwargs or {}
            )
        if result is not NotImplemented:
            return result

    # Default implementation
    device = None
    dtype = None
    non_blocking = False
    memory_format = None

    # Handle positional arguments
    if len(args) == 1:
        arg = args[0]
        # Check if it's a tensor
        if isinstance(arg, torch.Tensor):
            device = arg.device
            dtype = arg.dtype
        # Check if it's a dtype
        elif isinstance(arg, torch.dtype):
            dtype = arg
        # Check if it's a device (string or torch.device)
        elif isinstance(arg, (str, torch.device)):
            device = torch.device(arg) if isinstance(arg, str) else arg
        else:
            raise TypeError(
                f"to() received an invalid combination of arguments. Got: {type(arg)}"
            )
    elif len(args) > 1:
        raise TypeError(
            f"to() received too many positional arguments. Got {len(args)}, expected at most 1"
        )

    # Handle keyword arguments
    if "device" in kwargs:
        device_arg = kwargs["device"]
        if device_arg is not None:
            device = (
                torch.device(device_arg) if isinstance(device_arg, str) else device_arg
            )

    if "dtype" in kwargs:
        dtype = kwargs["dtype"]

    if "non_blocking" in kwargs:
        non_blocking = kwargs["non_blocking"]

    if "memory_format" in kwargs:
        memory_format = kwargs["memory_format"]

    # pyrefly: ignore[bad-return]
    return (device, dtype, non_blocking, memory_format)