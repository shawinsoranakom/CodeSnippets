def init_tornado_logs() -> None:
    """Set Tornado log levels.

    This function does not import any Tornado code, so it's safe to call even
    when Server is not running.
    """
    # http://www.tornadoweb.org/en/stable/log.html
    for log in ("access", "application", "general"):
        # get_logger will set the log level for the logger with the given name.
        get_logger(f"tornado.{log}")