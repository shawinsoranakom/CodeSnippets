def _strptime(data_string, format="%a %b %d %H:%M:%S %Y"):
    """Return a 3-tuple consisting of a tuple with time components,
    an int containing the number of microseconds, and an int
    containing the microseconds part of the GMT offset, based on the
    input string and the format string."""

    for index, arg in enumerate([data_string, format]):
        if not isinstance(arg, str):
            msg = "strptime() argument {} must be str, not {}"
            raise TypeError(msg.format(index, type(arg)))

    global _TimeRE_cache, _regex_cache
    with _cache_lock:
        locale_time = _TimeRE_cache.locale_time
        if (_getlang() != locale_time.lang or
            time.tzname != locale_time.tzname or
            time.daylight != locale_time.daylight):
            _TimeRE_cache = TimeRE()
            _regex_cache.clear()
            locale_time = _TimeRE_cache.locale_time
        if len(_regex_cache) > _CACHE_MAX_SIZE:
            _regex_cache.clear()
        format_regex = _regex_cache.get(format)
        if not format_regex:
            try:
                format_regex = _TimeRE_cache.compile(format)
            # KeyError raised when a bad format is found; can be specified as
            # \\, in which case it was a stray % but with a space after it
            except KeyError as err:
                bad_directive = err.args[0]
                del err
                bad_directive = bad_directive.replace('\\s', '')
                if not bad_directive:
                    raise ValueError("stray %% in format '%s'" % format) from None
                bad_directive = bad_directive.replace('\\', '', 1)
                raise ValueError("'%s' is a bad directive in format '%s'" %
                                    (bad_directive, format)) from None
            _regex_cache[format] = format_regex
    found = format_regex.match(data_string)
    if not found:
        raise ValueError("time data %r does not match format %r" %
                         (data_string, format))
    if len(data_string) != found.end():
        rest = data_string[found.end():]
        # Specific check for '%:z' directive
        if (
            "colon_z" in found.re.groupindex
            and found.group("colon_z") is not None
            and rest[0] != ":"
        ):
            raise ValueError(
                f"Missing colon in %:z before '{rest}', got '{data_string}'"
            )
        raise ValueError("unconverted data remains: %s" % rest)

    iso_year = year = None
    month = day = 1
    hour = minute = second = fraction = 0
    tz = -1
    gmtoff = None
    gmtoff_fraction = 0
    iso_week = week_of_year = None
    week_of_year_start = None
    # weekday and julian defaulted to None so as to signal need to calculate
    # values
    weekday = julian = None
    found_dict = found.groupdict()
    if locale_time.LC_alt_digits:
        def parse_int(s):
            try:
                return locale_time.LC_alt_digits.index(s)
            except ValueError:
                return int(s)
    else:
        parse_int = int

    for group_key in found_dict.keys():
        # Directives not explicitly handled below:
        #   c, x, X
        #      handled by making out of other directives
        #   U, W
        #      worthless without day of the week
        if group_key == 'y':
            year = parse_int(found_dict['y'])
            if 'C' in found_dict:
                century = parse_int(found_dict['C'])
                year += century * 100
            else:
                # Open Group specification for strptime() states that a %y
                #value in the range of [00, 68] is in the century 2000, while
                #[69,99] is in the century 1900
                if year <= 68:
                    year += 2000
                else:
                    year += 1900
        elif group_key == 'Y':
            year = int(found_dict['Y'])
        elif group_key == 'G':
            iso_year = int(found_dict['G'])
        elif group_key == 'm':
            month = parse_int(found_dict['m'])
        elif group_key == 'B':
            month = locale_time.f_month.index(found_dict['B'].lower())
        elif group_key == 'b':
            month = locale_time.a_month.index(found_dict['b'].lower())
        elif group_key == 'd':
            day = parse_int(found_dict['d'])
        elif group_key == 'H':
            hour = parse_int(found_dict['H'])
        elif group_key == 'I':
            hour = parse_int(found_dict['I'])
            ampm = found_dict.get('p', '').lower()
            # If there was no AM/PM indicator, we'll treat this like AM
            if ampm == locale_time.am_pm[1]:
                # We're in PM so we need to add 12 to the hour unless
                # we're looking at 12 noon.
                # 12 noon == 12 PM == hour 12
                if hour != 12:
                    hour += 12
            else:
                # We're in AM so the hour is correct unless we're
                # looking at 12 midnight.
                # 12 midnight == 12 AM == hour 0
                if hour == 12:
                    hour = 0
        elif group_key == 'M':
            minute = parse_int(found_dict['M'])
        elif group_key == 'S':
            second = parse_int(found_dict['S'])
        elif group_key == 'f':
            s = found_dict['f']
            # Pad to always return microseconds.
            s += "0" * (6 - len(s))
            fraction = int(s)
        elif group_key == 'A':
            weekday = locale_time.f_weekday.index(found_dict['A'].lower())
        elif group_key == 'a':
            weekday = locale_time.a_weekday.index(found_dict['a'].lower())
        elif group_key == 'w':
            weekday = int(found_dict['w'])
            if weekday == 0:
                weekday = 6
            else:
                weekday -= 1
        elif group_key == 'u':
            weekday = int(found_dict['u'])
            weekday -= 1
        elif group_key == 'j':
            julian = int(found_dict['j'])
        elif group_key in ('U', 'W'):
            week_of_year = int(found_dict[group_key])
            if group_key == 'U':
                # U starts week on Sunday.
                week_of_year_start = 6
            else:
                # W starts week on Monday.
                week_of_year_start = 0
        elif group_key == 'V':
            iso_week = int(found_dict['V'])
        elif group_key in ('z', 'colon_z'):
            z = found_dict[group_key]
            if z:
                if z == 'Z':
                    gmtoff = 0
                else:
                    if z[3] == ':':
                        z = z[:3] + z[4:]
                        if len(z) > 5:
                            if z[5] != ':':
                                msg = f"Inconsistent use of : in {found_dict[group_key]}"
                                raise ValueError(msg)
                            z = z[:5] + z[6:]
                    hours = int(z[1:3])
                    minutes = int(z[3:5])
                    seconds = int(z[5:7] or 0)
                    gmtoff = (hours * 60 * 60) + (minutes * 60) + seconds
                    gmtoff_remainder = z[8:]
                    # Pad to always return microseconds.
                    gmtoff_remainder_padding = "0" * (6 - len(gmtoff_remainder))
                    gmtoff_fraction = int(gmtoff_remainder + gmtoff_remainder_padding)
                    if z.startswith("-"):
                        gmtoff = -gmtoff
                        gmtoff_fraction = -gmtoff_fraction
        elif group_key == 'Z':
            # Since -1 is default value only need to worry about setting tz if
            # it can be something other than -1.
            found_zone = found_dict['Z'].lower()
            for value, tz_values in enumerate(locale_time.timezone):
                if found_zone in tz_values:
                    # Deal with bad locale setup where timezone names are the
                    # same and yet time.daylight is true; too ambiguous to
                    # be able to tell what timezone has daylight savings
                    if (time.tzname[0] == time.tzname[1] and
                       time.daylight and found_zone not in ("utc", "gmt")):
                        break
                    else:
                        tz = value
                        break

    # Deal with the cases where ambiguities arise
    # don't assume default values for ISO week/year
    if iso_year is not None:
        if julian is not None:
            raise ValueError("Day of the year directive '%j' is not "
                             "compatible with ISO year directive '%G'. "
                             "Use '%Y' instead.")
        elif iso_week is None or weekday is None:
            raise ValueError("ISO year directive '%G' must be used with "
                             "the ISO week directive '%V' and a weekday "
                             "directive ('%A', '%a', '%w', or '%u').")
    elif iso_week is not None:
        if year is None or weekday is None:
            raise ValueError("ISO week directive '%V' must be used with "
                             "the ISO year directive '%G' and a weekday "
                             "directive ('%A', '%a', '%w', or '%u').")
        else:
            raise ValueError("ISO week directive '%V' is incompatible with "
                             "the year directive '%Y'. Use the ISO year '%G' "
                             "instead.")

    leap_year_fix = False
    if year is None:
        if month == 2 and day == 29:
            year = 1904  # 1904 is first leap year of 20th century
            leap_year_fix = True
        else:
            year = 1900

    # If we know the week of the year and what day of that week, we can figure
    # out the Julian day of the year.
    if julian is None and weekday is not None:
        if week_of_year is not None:
            week_starts_Mon = True if week_of_year_start == 0 else False
            julian = _calc_julian_from_U_or_W(year, week_of_year, weekday,
                                                week_starts_Mon)
        elif iso_year is not None and iso_week is not None:
            datetime_result = datetime_date.fromisocalendar(iso_year, iso_week, weekday + 1)
            year = datetime_result.year
            month = datetime_result.month
            day = datetime_result.day
        if julian is not None and julian <= 0:
            year -= 1
            yday = 366 if calendar.isleap(year) else 365
            julian += yday

    if julian is None:
        # Cannot pre-calculate datetime_date() since can change in Julian
        # calculation and thus could have different value for the day of
        # the week calculation.
        # Need to add 1 to result since first day of the year is 1, not 0.
        julian = datetime_date(year, month, day).toordinal() - \
                  datetime_date(year, 1, 1).toordinal() + 1
    else:  # Assume that if they bothered to include Julian day (or if it was
           # calculated above with year/week/weekday) it will be accurate.
        datetime_result = datetime_date.fromordinal(
                            (julian - 1) +
                            datetime_date(year, 1, 1).toordinal())
        year = datetime_result.year
        month = datetime_result.month
        day = datetime_result.day
    if weekday is None:
        weekday = datetime_date(year, month, day).weekday()
    # Add timezone info
    tzname = found_dict.get("Z")

    if leap_year_fix:
        # the caller didn't supply a year but asked for Feb 29th. We couldn't
        # use the default of 1900 for computations. We set it back to ensure
        # that February 29th is smaller than March 1st.
        year = 1900

    return (year, month, day,
            hour, minute, second,
            weekday, julian, tz, tzname, gmtoff), fraction, gmtoff_fraction