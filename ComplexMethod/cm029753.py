def _isoweek_to_gregorian(year, week, day):
    # Year is bounded this way because 9999-12-31 is (9999, 52, 5)
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError(f"year must be in {MINYEAR}..{MAXYEAR}, not {year}")

    if not 0 < week < 53:
        out_of_range = True

        if week == 53:
            # ISO years have 53 weeks in them on years starting with a
            # Thursday and leap years starting on a Wednesday
            first_weekday = _ymd2ord(year, 1, 1) % 7
            if (first_weekday == 4 or (first_weekday == 3 and
                                       _is_leap(year))):
                out_of_range = False

        if out_of_range:
            raise ValueError(f"Invalid week: {week}")

    if not 0 < day < 8:
        raise ValueError(f"Invalid weekday: {day} (range is [1, 7])")

    # Now compute the offset from (Y, 1, 1) in days:
    day_offset = (week - 1) * 7 + (day - 1)

    # Calculate the ordinal day for monday, week 1
    day_1 = _isoweek1monday(year)
    ord_day = day_1 + day_offset

    return _ord2ymd(ord_day)