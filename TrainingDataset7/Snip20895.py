def myattr_dec(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper.myattr = True
    return wrapper