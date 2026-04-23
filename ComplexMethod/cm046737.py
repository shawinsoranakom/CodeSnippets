def _extract_column_value(val, col: str, label_mapping: dict) -> str:
    """Extract a string value from a column, handling complex types and label mapping."""
    # Handle complex types (dicts, lists) — extract useful text instead of raw repr
    if isinstance(val, dict):
        # Common pattern: {"text": [...]} in QA datasets
        if "text" in val:
            inner = val["text"]
            str_val = inner[0] if isinstance(inner, list) and inner else str(inner)
        else:
            str_val = json.dumps(val, ensure_ascii = False)
    elif isinstance(val, list):
        str_val = val[0] if len(val) == 1 else ", ".join(str(v) for v in val)
    else:
        str_val = str(val) if val is not None else ""

    # Apply label mapping if this column has one
    if col in label_mapping and isinstance(label_mapping[col], dict):
        str_val = label_mapping[col].get(str_val, str_val)

    return str_val