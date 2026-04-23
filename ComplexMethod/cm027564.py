def parse_datetime(dt_str: str, *, raise_on_error: bool = False) -> dt.datetime | None:
    """Parse a string and return a datetime.datetime.

    This function supports time zone offsets. When the input contains one,
    the output uses a timezone with a fixed offset from UTC.
    Raises ValueError if the input is well formatted but not a valid datetime.

    If the input isn't well formatted, returns None if raise_on_error is False
    or raises ValueError if it's True.
    """
    # First try if the string can be parsed by the fast ciso8601 library
    with suppress(ValueError, IndexError):
        return ciso8601.parse_datetime(dt_str)

    # ciso8601 failed to parse the string, fall back to regex
    if not (match := DATETIME_RE.match(dt_str)):
        if raise_on_error:
            raise ValueError
        return None
    kws: dict[str, Any] = match.groupdict()
    if kws["microsecond"]:
        kws["microsecond"] = kws["microsecond"].ljust(6, "0")
    tzinfo_str = kws.pop("tzinfo")

    tzinfo: dt.tzinfo | None = None
    if tzinfo_str == "Z":
        tzinfo = UTC
    elif tzinfo_str is not None:
        offset_mins = int(tzinfo_str[-2:]) if len(tzinfo_str) > 3 else 0
        offset_hours = int(tzinfo_str[1:3])
        offset = dt.timedelta(hours=offset_hours, minutes=offset_mins)
        if tzinfo_str[0] == "-":
            offset = -offset
        tzinfo = dt.timezone(offset)
    kws = {k: int(v) for k, v in kws.items() if v is not None}
    kws["tzinfo"] = tzinfo
    return dt.datetime(**kws)