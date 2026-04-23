def _exit(message):  # pragma: nocover
    """Exit program with error."""
    LOGGER.error(message)
    sys.exit(-1)