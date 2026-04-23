def _is_scalar_dtype_arg(arg: DTypeArg) -> bool:
    arg = _unwrap_dtype_arg(arg)
    if isinstance(arg, torch._prims_common.Number):
        return True

    is_scalar = getattr(arg, "is_scalar", False)
    if callable(is_scalar):
        if is_scalar():
            return True
    elif is_scalar:
        return True

    shape = getattr(arg, "shape", _MISSING_SHAPE)
    if shape is _MISSING_SHAPE:
        return False

    if shape is None:
        return True
    if not isinstance(shape, Sequence):
        return False

    return len(shape) == 0