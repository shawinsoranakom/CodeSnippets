def remove_boolean_dispatch_from_name(p) -> Any:
    """
    Some ops have a default string representation such as
    '<function boolean_dispatch.<locals>.fn at 0x7ff1106bf280>',
    this function replaces them with the hardcoded function names.
    """
    if p is F.fractional_max_pool2d:
        return "torch.nn.functional.fractional_max_pool2d"
    elif p is F.fractional_max_pool3d:
        return "torch.nn.functional.fractional_max_pool3d"
    elif p is F.max_pool1d:
        return "torch.nn.functional.max_pool1d"
    elif p is F.max_pool2d:
        return "torch.nn.functional.max_pool2d"
    elif p is F.max_pool3d:
        return "torch.nn.functional.max_pool3d"
    elif p is F.adaptive_max_pool1d:
        return "torch.nn.functional.adaptive_max_pool1d"
    elif p is F.adaptive_max_pool2d:
        return "torch.nn.functional.adaptive_max_pool2d"
    elif p is F.adaptive_max_pool3d:
        return "torch.nn.functional.adaptive_max_pool3d"
    if "boolean_dispatch" in str(p):
        raise AssertionError(
            f"{p} does not have a human readable representation in "
            + "quantization documentation"
        )
    return p