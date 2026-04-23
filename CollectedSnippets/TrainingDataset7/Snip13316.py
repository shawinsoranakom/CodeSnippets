def default_if_none(value, arg):
    """If value is None, use given default."""
    if value is None:
        return arg
    return value