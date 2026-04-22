def do(func):
            @functools.wraps(func)
            def wrapper_do(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper_do