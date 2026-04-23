def center(value, arg):
    """Center the value in a field of a given width."""
    width = int(arg)
    if width <= 0:
        return value
    return f"{value:^{width}}"