def swappable_dependency(value):
    """Turn a setting value into a dependency."""
    return SwappableTuple((value.split(".", 1)[0], "__first__"), value)