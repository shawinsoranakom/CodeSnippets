def capfirst(x):
    """Capitalize the first letter of a string."""
    if not x:
        return x
    if not isinstance(x, str):
        x = str(x)
    return x[0].upper() + x[1:]