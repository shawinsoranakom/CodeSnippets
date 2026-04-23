def parse_age_limit(s):
    # isinstance(False, int) is True. So type() must be used instead
    if type(s) is int:  # noqa: E721
        return s if 0 <= s <= 21 else None
    elif not isinstance(s, str):
        return None
    m = re.match(r'^(?P<age>\d{1,2})\+?$', s)
    if m:
        return int(m.group('age'))
    s = s.upper()
    if s in US_RATINGS:
        return US_RATINGS[s]
    m = re.match(r'^TV[_-]?({})$'.format('|'.join(k[3:] for k in TV_PARENTAL_GUIDELINES)), s)
    if m:
        return TV_PARENTAL_GUIDELINES['TV-' + m.group(1)]
    return None