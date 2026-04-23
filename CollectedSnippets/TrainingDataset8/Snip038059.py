def _log_if_error(fn: Callable[[], None]) -> None:
    try:
        fn()
    except Exception as e:
        _LOGGER.warning(e)