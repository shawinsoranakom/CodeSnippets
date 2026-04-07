def add_level_messages(storage):
    """
    Add 6 messages from different levels (including a custom one) to a storage
    instance.
    """
    storage.add(constants.INFO, "A generic info message")
    storage.add(29, "Some custom level")
    storage.add(constants.DEBUG, "A debugging message", extra_tags="extra-tag")
    storage.add(constants.WARNING, "A warning")
    storage.add(constants.ERROR, "An error")
    storage.add(constants.SUCCESS, "This was a triumph.")