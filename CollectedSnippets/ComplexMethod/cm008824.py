def unified_timestamp(date_str, day_first=True, tz_offset=0):
    if not isinstance(date_str, str):
        return None

    date_str = re.sub(r'\s+', ' ', re.sub(
        r'(?i)[,|]|(mon|tues?|wed(nes)?|thu(rs)?|fri|sat(ur)?|sun)(day)?', '', date_str))

    pm_delta = 12 if re.search(r'(?i)PM', date_str) else 0
    timezone, date_str = extract_timezone(
        date_str, default=dt.timedelta(hours=tz_offset) if tz_offset else None)

    # Remove AM/PM + timezone
    date_str = re.sub(r'(?i)\s*(?:AM|PM)(?:\s+[A-Z]+)?', '', date_str)

    # Remove unrecognized timezones from ISO 8601 alike timestamps
    m = re.search(r'\d{1,2}:\d{1,2}(?:\.\d+)?(?P<tz>\s*[A-Z]+)$', date_str)
    if m:
        date_str = date_str[:-len(m.group('tz'))]

    # Python only supports microseconds, so remove nanoseconds
    m = re.search(r'^([0-9]{4,}-[0-9]{1,2}-[0-9]{1,2}T[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}\.[0-9]{6})[0-9]+$', date_str)
    if m:
        date_str = m.group(1)

    for expression in date_formats(day_first):
        with contextlib.suppress(ValueError):
            dt_ = dt.datetime.strptime(date_str, expression) - timezone + dt.timedelta(hours=pm_delta)
            return calendar.timegm(dt_.timetuple())

    timetuple = email.utils.parsedate_tz(date_str)
    if timetuple:
        return calendar.timegm(timetuple) + pm_delta * 3600 - int(timezone.total_seconds())