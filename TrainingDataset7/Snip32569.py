def wrapper(*args, **kwargs):
        value = f(*args, **kwargs)
        return f"{value} -- common decorated."