def _parse_date_fmt():
        fmt = get_format("DATE_FORMAT")
        escaped = False
        for char in fmt:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char in "Yy":
                yield "year"
            elif char in "bEFMmNn":
                yield "month"
            elif char in "dj":
                yield "day"