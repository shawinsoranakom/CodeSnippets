def get_max_message_size_bytes() -> int:
    """Returns the max websocket message size in bytes.

    This will lazyload the value from the config and store it in the global symbol table.
    """
    global _max_message_size_bytes

    if _max_message_size_bytes is None:
        _max_message_size_bytes = config.get_option("server.maxMessageSize") * int(1e6)

    return _max_message_size_bytes