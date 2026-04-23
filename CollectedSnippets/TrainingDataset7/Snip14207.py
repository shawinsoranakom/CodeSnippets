def _to_tuple(s):
    t = s.split("=", 1)
    if len(t) == 2:
        return t[0].lower(), t[1]
    return t[0].lower(), True