def set_level(request, level):
    """
    Set the minimum level of messages to be recorded, and return ``True`` if
    the level was recorded successfully.

    If set to ``None``, use the default level (see the get_level() function).
    """
    if not hasattr(request, "_messages"):
        return False
    request._messages.level = level
    return True