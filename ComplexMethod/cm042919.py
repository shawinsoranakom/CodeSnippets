def to_serializable_dict(obj: Any) -> Dict:
    """
    Recursively convert an object to a serializable dictionary using {type, params} structure
    for complex objects.
    """
    if obj is None:
        return None

    # Handle basic types
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # Handle Enum
    if isinstance(obj, Enum):
        return {
            "type": obj.__class__.__name__,
            "params": obj.value
        }

    # Handle datetime objects
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()

    # Handle lists, tuples, and sets
    if isinstance(obj, (list, tuple, set)):
        return [to_serializable_dict(item) for item in obj]

    # Handle dictionaries - preserve them as-is
    if isinstance(obj, dict):
        return {
            "type": "dict",  # Mark as plain dictionary
            "value": {str(k): to_serializable_dict(v) for k, v in obj.items()}
        }

    # Handle class instances
    if hasattr(obj, '__class__'):
        # Get constructor signature
        sig = inspect.signature(obj.__class__.__init__)
        params = sig.parameters

        # Get current values
        current_values = {}
        for name, param in params.items():
            if name == 'self':
                continue

            value = getattr(obj, name, param.default)

            # Only include if different from default, considering empty values
            if not (is_empty_value(value) and is_empty_value(param.default)):
                if value != param.default:
                    current_values[name] = to_serializable_dict(value)

        return {
            "type": obj.__class__.__name__,
            "params": current_values
        }

    return str(obj)