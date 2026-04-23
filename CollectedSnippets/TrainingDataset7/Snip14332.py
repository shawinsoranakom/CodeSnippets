def parse_date(value):
    """Parse a string and return a datetime.date.

    Raise ValueError if the input is well formatted but not a valid date.
    Return None if the input isn't well formatted.
    """
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        if match := date_re.match(value):
            kw = {k: int(v) for k, v in match.groupdict().items()}
            return datetime.date(**kw)