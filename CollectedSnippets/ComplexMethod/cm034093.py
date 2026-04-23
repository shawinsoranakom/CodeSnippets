def boolean(value, strict=True):
    if isinstance(value, bool):
        return value

    normalized_value = value

    if isinstance(value, (str, bytes)):
        normalized_value = to_text(value, errors='surrogate_or_strict').lower().strip()

    if not isinstance(value, c.Hashable):
        normalized_value = None  # prevent unhashable types from bombing, but keep the rest of the existing fallback/error behavior

    if normalized_value in BOOLEANS_TRUE:
        return True
    elif normalized_value in BOOLEANS_FALSE or not strict:
        return False

    raise TypeError("The value '%s' is not a valid boolean. Valid booleans include: %s" % (to_text(value), ', '.join(repr(i) for i in BOOLEANS)))