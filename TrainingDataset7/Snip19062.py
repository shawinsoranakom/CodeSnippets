def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except AssertionError:
                    attempts += 1
                    if attempts >= retries:
                        raise
                    time.sleep(delay)

        return wrapper