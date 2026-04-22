def _delta_to_micros(delta: timedelta) -> int:
    return (
        delta.microseconds
        + delta.seconds * SECONDS_TO_MICROS
        + delta.days * DAYS_TO_MICROS
    )