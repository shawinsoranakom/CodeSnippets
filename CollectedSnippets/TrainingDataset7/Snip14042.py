def set_urlconf(urlconf_name):
    """
    Set the URLconf for the current thread or asyncio task (overriding the
    default one in settings). If urlconf_name is None, revert back to the
    default.
    """
    if urlconf_name:
        _urlconfs.value = urlconf_name
    else:
        if hasattr(_urlconfs, "value"):
            del _urlconfs.value