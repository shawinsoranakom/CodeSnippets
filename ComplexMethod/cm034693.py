def _sanitize_schema(schema: dict) -> dict:
    """Recursively remove JSON Schema keywords unsupported by the Gemini API."""
    if not isinstance(schema, dict):
        return schema
    result = {}
    for k, v in schema.items():
        if k in _UNSUPPORTED_SCHEMA_KEYS:
            continue
        if isinstance(v, dict):
            result[k] = _sanitize_schema(v)
        elif isinstance(v, list):
            result[k] = [_sanitize_schema(i) if isinstance(i, dict) else i for i in v]
        else:
            result[k] = v
    return result