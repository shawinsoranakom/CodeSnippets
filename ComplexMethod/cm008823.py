def extract_timezone(date_str, default=None):
    m = re.search(
        r'''(?x)
            ^.{8,}?                                              # >=8 char non-TZ prefix, if present
            (?P<tz>Z|                                            # just the UTC Z, or
                (?:(?<=.\b\d{4}|\b\d{2}:\d\d)|                   # preceded by 4 digits or hh:mm or
                   (?<!.\b[a-zA-Z]{3}|[a-zA-Z]{4}|..\b\d\d))     # not preceded by 3 alpha word or >= 4 alpha or 2 digits
                   [ ]?                                          # optional space
                (?P<sign>\+|-)                                   # +/-
                (?P<hours>[0-9]{2}):?(?P<minutes>[0-9]{2})       # hh[:]mm
            $)
        ''', date_str)
    timezone = None

    if not m:
        m = re.search(r'\d{1,2}:\d{1,2}(?:\.\d+)?(?P<tz>\s*[A-Z]+)$', date_str)
        timezone = TIMEZONE_NAMES.get(m and m.group('tz').strip())
        if timezone is not None:
            date_str = date_str[:-len(m.group('tz'))]
            timezone = dt.timedelta(hours=timezone)
    else:
        date_str = date_str[:-len(m.group('tz'))]
        if m.group('sign'):
            sign = 1 if m.group('sign') == '+' else -1
            timezone = dt.timedelta(
                hours=sign * int(m.group('hours')),
                minutes=sign * int(m.group('minutes')))

    if timezone is None and default is not NO_DEFAULT:
        timezone = default or dt.timedelta()

    return timezone, date_str