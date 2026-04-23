def check_same_device(*args, allow_cpu_scalar_tensors):
    """
    Checks that all Tensors in args have the same device.

    Raises a RuntimeError when:
      - args contains an object whose type is not Tensor or Number
      - two Tensor objects in args have different devices, unless one is a CPU scalar tensor and allow_cpu_scalar_tensors is True
    """
    # Short-circuits if all (one or fewer) arguments are trivially on the same device
    if len(args) <= 1:
        return

    # Note: cannot initialize device to the first arg's device (it may not have one)
    device = None
    # pyrefly: ignore [bad-assignment]
    for arg in args:
        if isinstance(arg, Number):
            continue
        elif isinstance(arg, TensorLike):
            if allow_cpu_scalar_tensors and is_cpu_scalar_tensor(arg):
                continue

            if device is None:
                device = arg.device

            if device != arg.device:
                msg = (
                    "Tensor on device "
                    + str(arg.device)
                    + " is not on the expected device "
                    + str(device)
                    + "!"
                )
                raise RuntimeError(msg)
        else:
            msg = (
                "Unexpected type when checking for same device, " + str(type(arg)) + "!"
            )
            raise RuntimeError(msg)