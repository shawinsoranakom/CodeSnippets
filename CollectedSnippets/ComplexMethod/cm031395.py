def _str2time(day, mon, yr, hr, min, sec, tz):
    yr = int(yr)
    if yr > datetime.MAXYEAR:
        return None

    # translate month name to number
    # month numbers start with 1 (January)
    try:
        mon = MONTHS_LOWER.index(mon.lower())+1
    except ValueError:
        # maybe it's already a number
        try:
            imon = int(mon)
        except ValueError:
            return None
        if 1 <= imon <= 12:
            mon = imon
        else:
            return None

    # make sure clock elements are defined
    if hr is None: hr = 0
    if min is None: min = 0
    if sec is None: sec = 0

    day = int(day)
    hr = int(hr)
    min = int(min)
    sec = int(sec)

    if yr < 1000:
        # find "obvious" year
        cur_yr = time.localtime(time.time())[0]
        m = cur_yr % 100
        tmp = yr
        yr = yr + cur_yr - m
        m = m - tmp
        if abs(m) > 50:
            if m > 0: yr = yr + 100
            else: yr = yr - 100

    # convert UTC time tuple to seconds since epoch (not timezone-adjusted)
    t = _timegm((yr, mon, day, hr, min, sec, tz))

    if t is not None:
        # adjust time using timezone string, to get absolute time since epoch
        if tz is None:
            tz = "UTC"
        tz = tz.upper()
        offset = offset_from_tz_string(tz)
        if offset is None:
            return None
        t = t - offset

    return t