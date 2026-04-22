def get_logger(name: str) -> logging.Logger:
    """Return a logger.

    Parameters
    ----------
    name : str
        The name of the logger to use. You should just pass in __name__.

    Returns
    -------
    Logger

    """
    if name in _loggers.keys():
        return _loggers[name]

    if name == "root":
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)

    logger.setLevel(_global_log_level)
    logger.propagate = False
    setup_formatter(logger)

    _loggers[name] = logger

    return logger