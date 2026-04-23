def get_language():
    """Return the currently selected language."""
    t = getattr(_active, "value", None)
    if t is not None:
        try:
            return t.to_language()
        except AttributeError:
            pass
    # If we don't have a real translation object, assume it's the default
    # language.
    return settings.LANGUAGE_CODE