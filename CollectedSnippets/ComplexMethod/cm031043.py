def normalize(obj: Any) -> Any:
    """Normalize test objects.

    This normalizes primitive values (e.g. floats)."""
    if isinstance(obj, list):
        return [normalize(item) for item in obj]
    if isinstance(obj, dict):
        if "type" in obj and "value" in obj:
            type_ = obj["type"]
            value = obj["value"]
            if type_ == "float":
                norm_value = _normalize_float_str(value)
            elif type_ in {"datetime", "datetime-local"}:
                norm_value = _normalize_datetime_str(value)
            elif type_ == "time-local":
                norm_value = _normalize_localtime_str(value)
            else:
                norm_value = value

            if type_ == "array":
                return [normalize(item) for item in value]
            return {"type": type_, "value": norm_value}
        return {k: normalize(v) for k, v in obj.items()}
    raise AssertionError("Burntsushi fixtures should be dicts/lists only")