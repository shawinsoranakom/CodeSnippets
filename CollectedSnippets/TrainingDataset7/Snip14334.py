def parse_datetime(value):
    """Parse a string and return a datetime.datetime.

    This function supports time zone offsets. When the input contains one,
    the output uses a timezone with a fixed offset from UTC.

    Raise ValueError if the input is well formatted but not a valid datetime.
    Return None if the input isn't well formatted.
    """
    try:
        return datetime.datetime.fromisoformat(value)
    except ValueError:
        if match := datetime_re.match(value):
            kw = match.groupdict()
            kw["microsecond"] = kw["microsecond"] and kw["microsecond"].ljust(6, "0")
            tzinfo = kw.pop("tzinfo")
            if tzinfo == "Z":
                tzinfo = datetime.UTC
            elif tzinfo is not None:
                offset_mins = int(tzinfo[-2:]) if len(tzinfo) > 3 else 0
                offset = 60 * int(tzinfo[1:3]) + offset_mins
                if tzinfo[0] == "-":
                    offset = -offset
                tzinfo = get_fixed_timezone(offset)
            kw = {k: int(v) for k, v in kw.items() if v is not None}
            return datetime.datetime(**kw, tzinfo=tzinfo)