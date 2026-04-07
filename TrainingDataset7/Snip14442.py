def lazystr(text):
    """
    Shortcut for the common case of a lazy callable that returns str.
    """
    return lazy(str, str)(text)