def update_formatter() -> None:
    for log in _loggers.values():
        setup_formatter(log)