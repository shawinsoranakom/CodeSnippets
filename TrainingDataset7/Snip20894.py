def simple_dec(func):
    @wraps(func)
    def wrapper(arg):
        return func("test:" + arg)

    return wrapper