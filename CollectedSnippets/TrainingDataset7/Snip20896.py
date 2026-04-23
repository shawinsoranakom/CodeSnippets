def myattr2_dec(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper.myattr2 = True
    return wrapper