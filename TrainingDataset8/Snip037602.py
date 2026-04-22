def _micros_to_datetime(micros: int, orig_tz: Optional[tzinfo]) -> datetime:
    """Restore times/datetimes to original timezone (dates are always naive)"""
    utc_dt = UTC_EPOCH + timedelta(microseconds=micros)
    # Add the original timezone. No conversion is required here,
    # since in the serialization, we also just replace the timestamp with UTC.
    return utc_dt.replace(tzinfo=orig_tz)