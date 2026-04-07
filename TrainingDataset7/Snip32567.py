def common_decorator(f):
    def wrapper(*args, **kwargs):
        value = f(*args, **kwargs)
        return f"{value} -- common decorated."

    return wrapper