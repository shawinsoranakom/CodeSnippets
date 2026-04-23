def set_log_level(level: Union[str, int]) -> None:
    """Set log level."""
    logger = get_logger(__name__)

    if isinstance(level, str):
        level = level.upper()
    if level == "CRITICAL" or level == logging.CRITICAL:
        log_level = logging.CRITICAL
    elif level == "ERROR" or level == logging.ERROR:
        log_level = logging.ERROR
    elif level == "WARNING" or level == logging.WARNING:
        log_level = logging.WARNING
    elif level == "INFO" or level == logging.INFO:
        log_level = logging.INFO
    elif level == "DEBUG" or level == logging.DEBUG:
        log_level = logging.DEBUG
    else:
        msg = 'undefined log level "%s"' % level
        logger.critical(msg)
        sys.exit(1)

    for log in _loggers.values():
        log.setLevel(log_level)

    global _global_log_level
    _global_log_level = log_level