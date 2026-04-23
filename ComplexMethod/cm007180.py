def serialize_for_json(obj: Any) -> Any:
    """Convert object to JSON-serializable format.

    Args:
        obj: Any object to serialize

    Returns:
        JSON-serializable representation of the object
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    if hasattr(obj, "model_dump"):
        return serialize_for_json(obj.model_dump())
    if hasattr(obj, "dict"):
        return serialize_for_json(obj.dict())
    try:
        return str(obj)
    except (TypeError, ValueError):
        return None