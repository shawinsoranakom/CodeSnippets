def wraps_decorator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        value = f(*args, **kwargs)
        return f"{value} -- decorated by @wraps."

    return wrapper