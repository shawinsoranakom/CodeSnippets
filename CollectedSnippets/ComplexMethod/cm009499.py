def _serialize_value(obj: Any) -> Any:
    """Serialize a value with escaping of user dicts.

    Called recursively on kwarg values to escape any plain dicts that could be confused
    with LC objects.

    Args:
        obj: The value to serialize.

    Returns:
        The serialized value with user dicts escaped as needed.
    """
    if isinstance(obj, Serializable):
        # This is an LC object - serialize it properly (not escaped)
        return _serialize_lc_object(obj)
    if isinstance(obj, dict):
        if not all(isinstance(k, (str, int, float, bool, type(None))) for k in obj):
            # if keys are not json serializable
            return to_json_not_implemented(obj)
        # Check if dict needs escaping BEFORE recursing into values.
        # If it needs escaping, wrap it as-is - the contents are user data that
        # will be returned as-is during deserialization (no instantiation).
        # This prevents re-escaping of already-escaped nested content.
        if _needs_escaping(obj):
            return _escape_dict(obj)
        # Safe dict (no 'lc' key) - recurse into values
        return {k: _serialize_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize_value(item) for item in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    # Non-JSON-serializable object (datetime, custom objects, etc.)
    return to_json_not_implemented(obj)