def _find_isoformat_datetime_separator(dtstr):
    # See the comment in _datetimemodule.c:_find_isoformat_datetime_separator
    len_dtstr = len(dtstr)
    if len_dtstr == 7:
        return 7

    assert len_dtstr > 7
    date_separator = "-"
    week_indicator = "W"

    if dtstr[4] == date_separator:
        if dtstr[5] == week_indicator:
            if len_dtstr < 8:
                raise ValueError("Invalid ISO string")
            if len_dtstr > 8 and dtstr[8] == date_separator:
                if len_dtstr == 9:
                    raise ValueError("Invalid ISO string")
                if len_dtstr > 10 and _is_ascii_digit(dtstr[10]):
                    # This is as far as we need to resolve the ambiguity for
                    # the moment - if we have YYYY-Www-##, the separator is
                    # either a hyphen at 8 or a number at 10.
                    #
                    # We'll assume it's a hyphen at 8 because it's way more
                    # likely that someone will use a hyphen as a separator than
                    # a number, but at this point it's really best effort
                    # because this is an extension of the spec anyway.
                    # TODO(pganssle): Document this
                    return 8
                return 10
            else:
                # YYYY-Www (8)
                return 8
        else:
            # YYYY-MM-DD (10)
            return 10
    else:
        if dtstr[4] == week_indicator:
            # YYYYWww (7) or YYYYWwwd (8)
            idx = 7
            while idx < len_dtstr:
                if not _is_ascii_digit(dtstr[idx]):
                    break
                idx += 1

            if idx < 9:
                return idx

            if idx % 2 == 0:
                # If the index of the last number is even, it's YYYYWwwd
                return 7
            else:
                return 8
        else:
            # YYYYMMDD (8)
            return 8