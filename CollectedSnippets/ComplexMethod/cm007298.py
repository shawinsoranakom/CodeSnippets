def parse_duration(s):
    if not isinstance(s, compat_basestring):
        return None

    s = s.strip()
    if not s:
        return None

    days, hours, mins, secs, ms = [None] * 5
    m = re.match(r'''(?x)
            (?P<before_secs>
                (?:(?:(?P<days>[0-9]+):)?(?P<hours>[0-9]+):)?
                (?P<mins>[0-9]+):)?
                (?P<secs>(?(before_secs)[0-9]{1,2}|[0-9]+))
            (?:[.:](?P<ms>[0-9]+))?Z?$
        ''', s)
    if m:
        days, hours, mins, secs, ms = m.group('days', 'hours', 'mins', 'secs', 'ms')
    else:
        m = re.match(
            r'''(?ix)(?:P?
                (?:
                    [0-9]+\s*y(?:ears?)?,?\s*
                )?
                (?:
                    [0-9]+\s*m(?:onths?)?,?\s*
                )?
                (?:
                    [0-9]+\s*w(?:eeks?)?,?\s*
                )?
                (?:
                    (?P<days>[0-9]+)\s*d(?:ays?)?,?\s*
                )?
                T)?
                (?:
                    (?P<hours>[0-9]+)\s*h(?:(?:ou)?rs?)?,?\s*
                )?
                (?:
                    (?P<mins>[0-9]+)\s*m(?:in(?:ute)?s?)?,?\s*
                )?
                (?:
                    (?P<secs>[0-9]+)(?:\.(?P<ms>[0-9]+))?\s*s(?:ec(?:ond)?s?)?\s*
                )?Z?$''', s)
        if m:
            days, hours, mins, secs, ms = m.group('days', 'hours', 'mins', 'secs', 'ms')
        else:
            m = re.match(r'(?i)(?:(?P<hours>[0-9.]+)\s*(?:hours?)|(?P<mins>[0-9.]+)\s*(?:mins?\.?|minutes?)\s*)Z?$', s)
            if m:
                hours, mins = m.groups()
            else:
                return None

    duration = (
        ((((float(days) * 24) if days else 0)
          + (float(hours) if hours else 0)) * 60
         + (float(mins) if mins else 0)) * 60
        + (float(secs) if secs else 0)
        + (float(ms) / 10 ** len(ms) if ms else 0))

    return duration