def convert_metadata_to_rows(key: str, value) -> list[dict]:
    """Turn a metadata key/value into typed projection rows."""
    if value is None:
        return []

    if _check_is_scalar(value):
        return [_scalar_to_row(key, 0, value)]

    if isinstance(value, list):
        if all(_check_is_scalar(x) for x in value):
            return [_scalar_to_row(key, i, x) for i, x in enumerate(value) if x is not None]
        return [{"key": key, "ordinal": i, "val_json": x} for i, x in enumerate(value) if x is not None]

    return [{"key": key, "ordinal": 0, "val_json": value}]