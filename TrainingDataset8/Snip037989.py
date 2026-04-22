def _get_type_name(obj: object) -> str:
    """Get a simplified name for the type of the given object."""
    with contextlib.suppress(Exception):
        obj_type = type(obj)
        type_name = "unknown"
        if hasattr(obj_type, "__qualname__"):
            type_name = obj_type.__qualname__
        elif hasattr(obj_type, "__name__"):
            type_name = obj_type.__name__

        if obj_type.__module__ != "builtins":
            # Add the full module path
            type_name = f"{obj_type.__module__}.{type_name}"

        if type_name in _OBJECT_NAME_MAPPING:
            type_name = _OBJECT_NAME_MAPPING[type_name]
        return type_name
    return "failed"