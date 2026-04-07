def catalog():
    """
    Return the current active catalog for further processing.
    This can be used if you need to modify the catalog or want to access the
    whole message catalog instead of just translating one string.
    """
    global _default

    t = getattr(_active, "value", None)
    if t is not None:
        return t
    if _default is None:
        _default = translation(settings.LANGUAGE_CODE)
    return _default