def translate_to_legacy[T: (dict[str, Any], list[Any], None)](raw: T) -> T:
    """Translate raw data to legacy format for dicts and lists."""

    if raw is None:
        return None

    if isinstance(raw, dict):
        return {TRANSLATION_MAP.get(k, k): v for k, v in raw.items()}

    if isinstance(raw, list):
        return [
            TRANSLATION_MAP[item]
            if isinstance(item, str) and item in TRANSLATION_MAP
            else item
            for item in raw
        ]

    return raw