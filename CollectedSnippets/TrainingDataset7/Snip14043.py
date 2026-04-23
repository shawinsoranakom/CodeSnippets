def get_urlconf(default=None):
    """
    Return the root URLconf to use for the current thread or asyncio task if it
    has been changed from the default one.
    """
    return getattr(_urlconfs, "value", default)