def get_level_tags():
    """
    Return the message level tags.
    """
    return {
        **constants.DEFAULT_TAGS,
        **getattr(settings, "MESSAGE_TAGS", {}),
    }