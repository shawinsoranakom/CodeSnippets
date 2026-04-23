def _get_type_name(t):
    """Get the type name of a type hint."""
    if hasattr(t, "__origin__"):
        if hasattr(t.__origin__, "__name__"):
            return f"{t.__origin__.__name__}[{', '.join([_get_type_name(arg) for arg in t.__args__])}]"
        if hasattr(t.__origin__, "_name"):
            return f"{t.__origin__._name}[{', '.join([_get_type_name(arg) for arg in t.__args__])}]"
    if isinstance(t, str):
        return t
    if hasattr(t, "__name__"):
        return t.__name__
    if hasattr(t, "_name"):
        return t._name
    return str(t)