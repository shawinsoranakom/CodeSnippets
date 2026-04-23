def _datetime_to_micros(dt: datetime) -> int:
    # The frontend is not aware of timezones and only expects a UTC-based
    # timestamp (in microseconds). Since we want to show the date/time exactly
    # as it is in the given datetime object, we just set the tzinfo to UTC and
    # do not do any timezone conversions. Only the backend knows about
    # original timezone and will replace the UTC timestamp in the deserialization.
    utc_dt = dt.replace(tzinfo=timezone.utc)
    return _delta_to_micros(utc_dt - UTC_EPOCH)