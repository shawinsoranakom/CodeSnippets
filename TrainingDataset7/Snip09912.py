def _sqlite_timestamp_diff(lhs, rhs):
    if lhs is None or rhs is None:
        return None
    left = typecast_timestamp(lhs)
    right = typecast_timestamp(rhs)
    return duration_microseconds(left - right)