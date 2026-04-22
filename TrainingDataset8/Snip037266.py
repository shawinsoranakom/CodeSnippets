def _logger_message_format() -> str:
    """String format for logging messages. If logger.datetimeFormat is set,
    logger messages will default to `%(asctime)s.%(msecs)03d %(message)s`. See
    [Python's documentation](https://docs.python.org/2.6/library/logging.html#formatter-objects)
    for available attributes.

    Default: "%(asctime)s %(message)s"
    """
    if get_option("global.developmentMode"):
        from streamlit.logger import DEFAULT_LOG_MESSAGE

        return DEFAULT_LOG_MESSAGE
    else:
        return "%(asctime)s %(message)s"