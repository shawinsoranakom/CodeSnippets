def _serialize_value(value: Any) -> Any:
    """Convert database-specific types to JSON-serializable Python types."""
    if isinstance(value, Decimal):
        # NaN / Infinity are not valid JSON numbers; serialize as strings.
        if value.is_nan() or value.is_infinite():
            return str(value)
        # Use int for whole numbers; use str for fractional to preserve exact
        # precision (float would silently round high-precision analytics values).
        if value == value.to_integral_value():
            return int(value)
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, memoryview):
        return bytes(value).hex()
    if isinstance(value, bytes):
        return value.hex()
    return value