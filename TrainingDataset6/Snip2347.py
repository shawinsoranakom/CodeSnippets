def eager(fn, *args, **kwargs):
    return list(fn(*args, **kwargs))