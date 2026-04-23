def is_relative_to(path: Path, *other):
    """Return True if the path is relative to another path or False.

    This function is backported from Python 3.9 - Path.relativeto.
    """
    try:
        path.relative_to(*other)
        return True
    except ValueError:
        return False