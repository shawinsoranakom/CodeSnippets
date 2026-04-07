def _sqlite_datetime_cast_time(dt, tzname, conn_tzname):
    dt = _sqlite_datetime_parse(dt, tzname, conn_tzname)
    if dt is None:
        return None
    return dt.time().isoformat()