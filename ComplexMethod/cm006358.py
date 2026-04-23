def _sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize a dictionary, masking sensitive values."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key in EXCLUDED_KEYS:
            continue
        if _is_sensitive_key(key):
            if isinstance(value, str) and value:
                result[key] = _mask_sensitive_value(value)
            else:
                result[key] = "***REDACTED***"
        elif isinstance(value, dict):
            result[key] = _sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = _sanitize_list(value)
        else:
            result[key] = value
    return result