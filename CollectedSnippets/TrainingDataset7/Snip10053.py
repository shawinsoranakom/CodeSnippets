def typecast_timestamp(s):  # does NOT store time zone information
    # "2005-07-29 15:48:00.590358-05"
    # "2005-07-29 09:56:00-05"
    if not s:
        return None
    if " " not in s:
        return typecast_date(s)
    d, t = s.split()
    # Remove timezone information.
    if "-" in t:
        t, _ = t.split("-", 1)
    elif "+" in t:
        t, _ = t.split("+", 1)
    dates = d.split("-")
    times = t.split(":")
    seconds = times[2]
    if "." in seconds:  # check whether seconds have a fractional part
        seconds, microseconds = seconds.split(".")
    else:
        microseconds = "0"
    return datetime.datetime(
        int(dates[0]),
        int(dates[1]),
        int(dates[2]),
        int(times[0]),
        int(times[1]),
        int(seconds),
        int((microseconds + "000000")[:6]),
    )