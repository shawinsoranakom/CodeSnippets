def sanitize_bytes_for_json(obj: Any) -> Any:
    """
    Recursively convert bytes objects to strings to ensure JSON serializability.

    Args:
        obj: Any object that might contain bytes

    Returns:
        Object with all bytes converted to strings
    """
    if isinstance(obj, bytes):
        try:
            # Try to decode as UTF-8 text first
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            # If not valid UTF-8, encode as base64 string
            return base64.b64encode(obj).decode('ascii')
    elif isinstance(obj, dict):
        return {key: sanitize_bytes_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_bytes_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_bytes_for_json(item) for item in obj)
    else:
        return obj