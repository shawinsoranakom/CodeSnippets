def redact_keys(data: Any, ids: dict[str, Any]) -> Any:
    """Redact sensitive keys in a dict."""
    if not isinstance(data, (Mapping, list)):
        return data

    if isinstance(data, list):
        return [redact_keys(val, ids) for val in data]

    redacted = {**data}

    keys = list(redacted)
    for key in keys:
        if key in ids:
            redacted[ids[key]] = redacted.pop(key)
        elif isinstance(redacted[key], Mapping):
            redacted[key] = redact_keys(redacted[key], ids)
        elif isinstance(redacted[key], list):
            redacted[key] = [redact_keys(item, ids) for item in redacted[key]]

    return redacted