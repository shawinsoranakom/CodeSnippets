def handle_uncaught_app_exception(ex: BaseException) -> None:
    """Handle an exception that originated from a user app.

    By default, we show exceptions directly in the browser. However,
    if the user has disabled client error details, we display a generic
    warning in the frontend instead.
    """

    error_logged = False

    if config.get_option("logger.enableRich"):
        try:
            # Print exception via rich
            # Rich is only a soft dependency
            # -> if not installed, we will use the default traceback formatting
            _print_rich_exception(ex)
            error_logged = True
        except Exception:
            # Rich is not installed or not compatible to our config
            # -> Use normal traceback formatting as fallback
            # Catching all exceptions because we don't want to leave any possibility of breaking here.
            error_logged = False

    if config.get_option("client.showErrorDetails"):
        if not error_logged:
            # TODO: Clean up the stack trace, so it doesn't include ScriptRunner.
            _LOGGER.warning("Uncaught app exception", exc_info=ex)
        st.exception(ex)
    else:
        if not error_logged:
            # Use LOGGER.error, rather than LOGGER.debug, since we don't
            # show debug logs by default.
            _LOGGER.error("Uncaught app exception", exc_info=ex)
        st.exception(UncaughtAppException(ex))