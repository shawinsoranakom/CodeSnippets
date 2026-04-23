def _type_to_str(t: Any) -> str:
    """Return a Python source expression for *t* suitable for exec'd schema code."""
    if t is type(None):
        return "None"
    if t is typing.Any:
        return "Any"
    if t in (int, float, bool, str, bytes):
        return t.__name__
    if t is pw.Pointer:
        return "pw.Pointer"
    if t is pw.Json:
        return "pw.Json"
    if t is pw.Duration:
        return "pw.Duration"
    if t is pw.DateTimeNaive:
        return "pw.DateTimeNaive"
    if t is pw.DateTimeUtc:
        return "pw.DateTimeUtc"

    origin = get_origin(t)
    args = get_args(t)

    if origin is Union or (
        hasattr(builtin_types, "UnionType") and isinstance(t, builtin_types.UnionType)
    ):
        return " | ".join(_type_to_str(a) for a in args)

    if origin is list:
        return f"list[{_type_to_str(args[0])}]"

    if origin is tuple:
        return f"tuple[{', '.join(_type_to_str(a) for a in args)}]"

    if origin is np.ndarray:
        dims_arg, scalar_arg = args
        scalar_str = _type_to_str(scalar_arg)
        if dims_arg is None:
            return f"np.ndarray[None, {scalar_str}]"
        return f"np.ndarray[{_type_to_str(dims_arg)}, {scalar_str}]"

    # pw.PyObjectWrapper[X]
    if origin is pw.PyObjectWrapper and args:
        return f"pw.PyObjectWrapper[{args[0].__name__}]"

    if hasattr(t, "__name__"):
        return t.__name__
    return repr(t)