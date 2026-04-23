def _is_supported_types(arg) -> bool:
    if isinstance(arg, list):
        return (
            all(_is_supported_types(a) for a in arg)
            and len({type(a) for a in arg}) <= 1
        )
    elif isinstance(arg, tuple):
        return all(_is_supported_types(a) for a in arg)
    elif isinstance(arg, dict):
        return (
            all(_is_supported_types(a) for a in arg.values())
            and len({type(a) for a in arg.values()}) <= 1
        )
    elif isinstance(arg, (torch.Tensor, int, float, bool, str)):
        return True
    elif arg is None:
        return True
    else:
        return False