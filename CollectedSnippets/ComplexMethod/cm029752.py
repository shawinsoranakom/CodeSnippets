def _parse_isoformat_time(tstr):
    # Format supported is HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]
    len_str = len(tstr)
    if len_str < 2:
        raise ValueError("Isoformat time too short")

    # This is equivalent to re.search('[+-Z]', tstr), but faster
    tz_pos = (tstr.find('-') + 1 or tstr.find('+') + 1 or tstr.find('Z') + 1)
    timestr = tstr[:tz_pos-1] if tz_pos > 0 else tstr

    time_comps = _parse_hh_mm_ss_ff(timestr)

    hour, minute, second, microsecond = time_comps
    became_next_day = False
    error_from_components = False
    error_from_tz = None
    if (hour == 24):
        if all(time_comp == 0 for time_comp in time_comps[1:]):
            hour = 0
            time_comps[0] = hour
            became_next_day = True
        else:
            error_from_components = True

    tzi = None
    if tz_pos == len_str and tstr[-1] == 'Z':
        tzi = timezone.utc
    elif tz_pos > 0:
        tzstr = tstr[tz_pos:]

        # Valid time zone strings are:
        # HH                  len: 2
        # HHMM                len: 4
        # HH:MM               len: 5
        # HHMMSS              len: 6
        # HHMMSS.f+           len: 7+
        # HH:MM:SS            len: 8
        # HH:MM:SS.f+         len: 10+

        if len(tzstr) in (0, 1, 3) or tstr[tz_pos-1] == 'Z':
            raise ValueError("Malformed time zone string")

        tz_comps = _parse_hh_mm_ss_ff(tzstr)

        if all(x == 0 for x in tz_comps):
            tzi = timezone.utc
        else:
            tzsign = -1 if tstr[tz_pos - 1] == '-' else 1

            try:
                # This function is intended to validate datetimes, but because
                # we restrict time zones to ±24h, it serves here as well.
                _check_time_fields(hour=tz_comps[0], minute=tz_comps[1],
                                   second=tz_comps[2], microsecond=tz_comps[3],
                                   fold=0)
            except ValueError as e:
                error_from_tz = e
            else:
                td = timedelta(hours=tz_comps[0], minutes=tz_comps[1],
                               seconds=tz_comps[2], microseconds=tz_comps[3])
                tzi = timezone(tzsign * td)

    time_comps.append(tzi)

    return time_comps, became_next_day, error_from_components, error_from_tz