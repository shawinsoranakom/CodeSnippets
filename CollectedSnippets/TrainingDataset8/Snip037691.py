def setup_formatter(logger: logging.Logger) -> None:
    """Set up the console formatter for a given logger."""

    # Deregister any previous console loggers.
    if hasattr(logger, "streamlit_console_handler"):
        logger.removeHandler(logger.streamlit_console_handler)

    logger.streamlit_console_handler = logging.StreamHandler()  # type: ignore[attr-defined]

    # Import here to avoid circular imports
    from streamlit import config

    if config._config_options:
        # logger is required in ConfigOption.set_value
        # Getting the config option before the config file has been parsed
        # can create an infinite loop
        message_format = config.get_option("logger.messageFormat")
    else:
        message_format = DEFAULT_LOG_MESSAGE
    formatter = logging.Formatter(fmt=message_format)
    formatter.default_msec_format = "%s.%03d"
    logger.streamlit_console_handler.setFormatter(formatter)  # type: ignore[attr-defined]

    # Register the new console logger.
    logger.addHandler(logger.streamlit_console_handler)