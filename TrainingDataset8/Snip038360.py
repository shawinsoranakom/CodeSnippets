def _set_up_signal_handler(server: Server) -> None:
    LOGGER.debug("Setting up signal handler")

    def signal_handler(signal_number, stack_frame):
        # The server will shut down its threads and exit its loop.
        server.stop()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)
    else:
        signal.signal(signal.SIGQUIT, signal_handler)