def _sqlite_mod(x, y):
    if x is None or y is None:
        return None
    return fmod(x, y)