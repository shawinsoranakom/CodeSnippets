def passthrough(f):
    @functools.wraps(f)
    def method(*args, **kwargs):
        return f(*args, **kwargs)

    return method