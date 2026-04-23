def to_list(value):
    """Put value into a list if it's not already one."""
    if not isinstance(value, list):
        value = [value]
    return value