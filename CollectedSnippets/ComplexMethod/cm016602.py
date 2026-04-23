def get_module_type_info(module: nn.Module) -> dict:
    """
    Determine module type and extract conv parameters from module class.

    This is more reliable than checking weight.ndim, especially for quantized layers
    where weight shape might be different.

    Returns:
        dict with keys: is_conv, conv_dim, stride, padding, dilation, groups
    """
    info = {
        "is_conv": False,
        "conv_dim": 0,
        "stride": (1,),
        "padding": (0,),
        "dilation": (1,),
        "groups": 1,
        "kernel_size": (1,),
        "in_channels": None,
        "out_channels": None,
    }

    # Determine conv type
    if isinstance(module, nn.Conv1d):
        info["is_conv"] = True
        info["conv_dim"] = 1
    elif isinstance(module, nn.Conv2d):
        info["is_conv"] = True
        info["conv_dim"] = 2
    elif isinstance(module, nn.Conv3d):
        info["is_conv"] = True
        info["conv_dim"] = 3
    elif isinstance(module, nn.Linear):
        info["is_conv"] = False
        info["conv_dim"] = 0
    else:
        # Try to infer from class name for custom/quantized layers
        class_name = type(module).__name__.lower()
        if "conv3d" in class_name:
            info["is_conv"] = True
            info["conv_dim"] = 3
        elif "conv2d" in class_name:
            info["is_conv"] = True
            info["conv_dim"] = 2
        elif "conv1d" in class_name:
            info["is_conv"] = True
            info["conv_dim"] = 1
        elif "conv" in class_name:
            info["is_conv"] = True
            info["conv_dim"] = 2

    # Extract conv parameters if it's a conv layer
    if info["is_conv"]:
        # Try to get stride, padding, dilation, groups, kernel_size from module
        info["stride"] = getattr(module, "stride", (1,) * info["conv_dim"])
        info["padding"] = getattr(module, "padding", (0,) * info["conv_dim"])
        info["dilation"] = getattr(module, "dilation", (1,) * info["conv_dim"])
        info["groups"] = getattr(module, "groups", 1)
        info["kernel_size"] = getattr(module, "kernel_size", (1,) * info["conv_dim"])
        info["in_channels"] = getattr(module, "in_channels", None)
        info["out_channels"] = getattr(module, "out_channels", None)

        # Ensure they're tuples
        if isinstance(info["stride"], int):
            info["stride"] = (info["stride"],) * info["conv_dim"]
        if isinstance(info["padding"], int):
            info["padding"] = (info["padding"],) * info["conv_dim"]
        if isinstance(info["dilation"], int):
            info["dilation"] = (info["dilation"],) * info["conv_dim"]
        if isinstance(info["kernel_size"], int):
            info["kernel_size"] = (info["kernel_size"],) * info["conv_dim"]

    return info