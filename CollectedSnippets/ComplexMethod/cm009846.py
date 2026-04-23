def _recursive_dump(obj: Any) -> Any:
    """Recursively dump the object if encountering any pydantic models."""
    if isinstance(obj, dict):
        return {
            k: _recursive_dump(v)
            for k, v in obj.items()
            if k != "id"  # Remove the id field for testing purposes
        }
    if isinstance(obj, list):
        return [_recursive_dump(v) for v in obj]
    if hasattr(obj, "dict"):
        # if the object contains an ID field, we'll remove it for testing purposes
        if hasattr(obj, "id"):
            d = obj.model_dump()
            d.pop("id")
            return _recursive_dump(d)
        return _recursive_dump(obj.model_dump())
    return obj