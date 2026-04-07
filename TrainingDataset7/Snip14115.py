def to_path(value):
    """Convert value to a pathlib.Path instance, if not already a Path."""
    if isinstance(value, Path):
        return value
    elif not isinstance(value, str):
        raise TypeError("Invalid path type: %s" % type(value).__name__)
    return Path(value)