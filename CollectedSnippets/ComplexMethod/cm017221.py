def _sqlite_datetime_parse(dt, tzname=None, conn_tzname=None):
    if dt is None:
        return None
    try:
        dt = typecast_timestamp(dt)
    except (TypeError, ValueError):
        return None
    if conn_tzname:
        dt = dt.replace(tzinfo=zoneinfo.ZoneInfo(conn_tzname))
    if tzname is not None and tzname != conn_tzname:
        tzname, sign, offset = split_tzname_delta(tzname)
        if offset:
            hours, minutes = offset.split(":")
            offset_delta = timedelta(hours=int(hours), minutes=int(minutes))
            dt += offset_delta if sign == "+" else -offset_delta
        # The tzname may originally be just the offset e.g. "+3:00",
        # which becomes an empty string after splitting the sign and offset.
        # In this case, use the conn_tzname as fallback.
        dt = timezone.localtime(dt, zoneinfo.ZoneInfo(tzname or conn_tzname))
    return dt