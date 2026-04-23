def redact_values(data: Any, ids: dict[str, Any]) -> Any:
    """Redact sensitive values in a dict."""
    if not isinstance(data, (Mapping, list)):
        if data in ids:
            return ids[data]
        return data

    if isinstance(data, list):
        return [redact_values(val, ids) for val in data]

    redacted = {**data}

    for key, value in redacted.items():
        if value is None:
            continue
        if isinstance(value, Mapping):
            redacted[key] = redact_values(value, ids)
        elif isinstance(value, list):
            redacted[key] = [redact_values(item, ids) for item in value]
        elif value in ids:
            redacted[key] = ids[value]

    return redacted