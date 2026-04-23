def typecast_time(s):  # does NOT store time zone information
    if not s:
        return None
    hour, minutes, seconds = s.split(":")
    if "." in seconds:  # check whether seconds have a fractional part
        seconds, microseconds = seconds.split(".")
    else:
        microseconds = "0"
    return datetime.time(
        int(hour), int(minutes), int(seconds), int((microseconds + "000000")[:6])
    )