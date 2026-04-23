def _summarize_binary_fields(raw_json: str) -> str:
    """Replace known binary fields with a size summary so truncate() doesn't
    produce garbled base64 in the middle-out preview."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return raw_json

    if not isinstance(data, dict):
        return raw_json

    changed = False
    for key in _BINARY_FIELD_NAMES:
        if key in data and isinstance(data[key], str) and len(data[key]) > 1_000:
            byte_size = len(data[key]) * 3 // 4  # approximate decoded size
            data[key] = f"<binary, ~{byte_size:,} bytes>"
            changed = True

    return json.dumps(data, ensure_ascii=False) if changed else raw_json