def get_level(request):
    """
    Return the minimum level of messages to be recorded.

    The default level is the ``MESSAGE_LEVEL`` setting. If this is not found,
    use the ``INFO`` level.
    """
    storage = getattr(request, "_messages", default_storage(request))
    return storage.level