def extract_size_bytes(obj: Mapping[str, Any]) -> int | None:
    """Extract size bytes from object metadata"""
    candidate_keys = (
        "Size",
        "size",
        "ContentLength",
        "content_length",
        "Content-Length",
        "contentLength",
        "bytes",
        "Bytes",
    )

    def _normalize(value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, Integral):
            return int(value)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if numeric >= 0 and numeric.is_integer():
            return int(numeric)
        return None

    for key in candidate_keys:
        if key in obj:
            normalized = _normalize(obj.get(key))
            if normalized is not None:
                return normalized

    for key, value in obj.items():
        if not isinstance(key, str):
            continue
        lowered_key = key.lower()
        if "size" in lowered_key or "length" in lowered_key:
            normalized = _normalize(value)
            if normalized is not None:
                return normalized

    return None