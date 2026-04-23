def _wrap_strftime(object, format, timetuple):
    # Don't call utcoffset() or tzname() unless actually needed.
    freplace = None  # the string to use for %f
    zreplace = None  # the string to use for %z
    colonzreplace = None  # the string to use for %:z
    Zreplace = None  # the string to use for %Z

    # Scan format for %z, %:z and %Z escapes, replacing as needed.
    newformat = []
    push = newformat.append
    i, n = 0, len(format)
    while i < n:
        ch = format[i]
        i += 1
        if ch == '%':
            if i < n:
                ch = format[i]
                i += 1
                if ch == 'f':
                    if freplace is None:
                        freplace = '%06d' % getattr(object,
                                                    'microsecond', 0)
                    newformat.append(freplace)
                elif ch == 'z':
                    if zreplace is None:
                        if hasattr(object, "utcoffset"):
                            zreplace = _format_offset(object.utcoffset(), sep="")
                        else:
                            zreplace = ""
                    assert '%' not in zreplace
                    newformat.append(zreplace)
                elif ch == ':':
                    if i < n:
                        ch2 = format[i]
                        i += 1
                        if ch2 == 'z':
                            if colonzreplace is None:
                                if hasattr(object, "utcoffset"):
                                    colonzreplace = _format_offset(object.utcoffset(), sep=":")
                                else:
                                    colonzreplace = ""
                            assert '%' not in colonzreplace
                            newformat.append(colonzreplace)
                        else:
                            push('%')
                            push(ch)
                            push(ch2)
                elif ch == 'Z':
                    if Zreplace is None:
                        Zreplace = ""
                        if hasattr(object, "tzname"):
                            s = object.tzname()
                            if s is not None:
                                # strftime is going to have at this: escape %
                                Zreplace = s.replace('%', '%%')
                    newformat.append(Zreplace)
                # Note that datetime(1000, 1, 1).strftime('%G') == '1000' so
                # year 1000 for %G can go on the fast path.
                elif ((ch in 'YG' or ch in 'FC') and
                        object.year < 1000 and _need_normalize_century()):
                    if ch == 'G':
                        year = int(_time.strftime("%G", timetuple))
                    else:
                        year = object.year
                    if ch == 'C':
                        push('{:02}'.format(year // 100))
                    else:
                        push('{:04}'.format(year))
                        if ch == 'F':
                            push('-{:02}-{:02}'.format(*timetuple[1:3]))
                else:
                    push('%')
                    push(ch)
            else:
                push('%')
        else:
            push(ch)
    newformat = "".join(newformat)
    return _time.strftime(newformat, timetuple)