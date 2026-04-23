def _sqlite_sign(x):
    if x is None:
        return None
    return (x > 0) - (x < 0)