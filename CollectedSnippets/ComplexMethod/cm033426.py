def serialize_for_json(obj):
    """
    Recursively serialize objects to make them JSON serializable.
    Handles ModelMetaclass and other non-serializable objects.
    """
    if hasattr(obj, "__dict__"):
        # For objects with __dict__, try to serialize their attributes
        try:
            return {key: serialize_for_json(value) for key, value in obj.__dict__.items() if not key.startswith("_")}
        except (AttributeError, TypeError):
            return str(obj)
    elif hasattr(obj, "__name__"):
        # For classes and metaclasses, return their name
        return f"<{obj.__module__}.{obj.__name__}>" if hasattr(obj, "__module__") else f"<{obj.__name__}>"
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        # Fallback: convert to string representation
        return str(obj)