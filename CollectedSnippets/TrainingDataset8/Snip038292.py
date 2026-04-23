def memoize(func):
    """Decorator to memoize the result of a no-args func."""
    result = []  # type: List[Any]

    @functools.wraps(func)
    def wrapped_func():
        if not result:
            result.append(func())
        return result[0]

    return wrapped_func