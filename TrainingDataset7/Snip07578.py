def update_level_tags(setting, **kwargs):
    if setting == "MESSAGE_TAGS":
        base.LEVEL_TAGS = SimpleLazyObject(get_level_tags)