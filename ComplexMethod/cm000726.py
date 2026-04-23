def _convert_bools(
    obj: Any,
) -> Any:  # noqa: ANN401 – allow Any for deep conversion utility
    """Recursively walk *obj* and coerce string booleans to real booleans."""
    if isinstance(obj, str):
        lowered = obj.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return obj
    if isinstance(obj, list):
        return [_convert_bools(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _convert_bools(v) for k, v in obj.items()}
    return obj