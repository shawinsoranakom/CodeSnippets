def _to_json_serializable(value: Any) -> Any:
    """Recursively convert value to a JSON-serializable form matching Pathway's
    MSSQL list/tuple serialization (serialize_value_to_json in data_format.rs)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, pw.Pointer):
        return str(value)
    if isinstance(value, pw.Json):
        return value.value  # the underlying JSON-compatible Python object
    if isinstance(value, pd.Timedelta):
        return value.value  # nanoseconds (serialize_value_to_json uses nanoseconds)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_to_json_serializable(v) for v in value]
    return value