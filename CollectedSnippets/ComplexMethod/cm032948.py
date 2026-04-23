def validate_tag_features(raw):
    if raw is None:
        return None

    if not isinstance(raw, dict):
        raise ValueError("must be an object mapping string tags to finite numeric scores")

    cleaned = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            raise ValueError("keys must be strings")
        key = key.strip()
        if not key:
            raise ValueError("keys must be non-empty strings")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("values must be finite numbers")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError("values must be finite numbers")
        cleaned[key] = numeric

    return cleaned