def _sqlite_log(base, x):
    if base is None or x is None:
        return None
    # Arguments reversed to match SQL standard.
    return log(x, base)