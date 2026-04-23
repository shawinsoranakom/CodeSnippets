def parse_age_limit(s):
    if not isinstance(s, bool):
        age = int_or_none(s)
        if age is not None:
            return age if 0 <= age <= 21 else None
    if not isinstance(s, compat_basestring):
        return None
    m = re.match(r'^(?P<age>\d{1,2})\+?$', s)
    if m:
        return int(m.group('age'))
    if s in US_RATINGS:
        return US_RATINGS[s]
    m = re.match(r'^TV[_-]?(%s)$' % '|'.join(k[3:] for k in TV_PARENTAL_GUIDELINES), s)
    if m:
        return TV_PARENTAL_GUIDELINES['TV-' + m.group(1)]
    return None