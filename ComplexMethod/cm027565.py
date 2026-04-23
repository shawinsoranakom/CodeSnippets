def parse_duration(value: str) -> dt.timedelta | None:
    """Parse a duration string and return a datetime.timedelta.

    Also supports ISO 8601 representation and PostgreSQL's day-time interval
    format.
    """
    match = (
        STANDARD_DURATION_RE.match(value)
        or ISO8601_DURATION_RE.match(value)
        or POSTGRES_INTERVAL_RE.match(value)
    )
    if match:
        kws = match.groupdict()
        sign = -1 if kws.pop("sign", "+") == "-" else 1
        if kws.get("microseconds"):
            kws["microseconds"] = kws["microseconds"].ljust(6, "0")
        time_delta_args: dict[str, float] = {
            k: float(v.replace(",", ".")) for k, v in kws.items() if v is not None
        }
        days = dt.timedelta(float(time_delta_args.pop("days", 0.0) or 0.0))
        if match.re == ISO8601_DURATION_RE:
            days *= sign
        return days + sign * dt.timedelta(**time_delta_args)
    return None