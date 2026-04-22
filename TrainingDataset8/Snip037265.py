def _logger_log_level() -> str:
    """Level of logging: 'error', 'warning', 'info', or 'debug'.

    Default: 'info'
    """

    if get_option("global.logLevel"):
        return str(get_option("global.logLevel"))
    elif get_option("global.developmentMode"):
        return "debug"
    else:
        return "info"