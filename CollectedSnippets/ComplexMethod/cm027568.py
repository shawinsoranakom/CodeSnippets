def deadlock_safe_shutdown() -> None:
    """Shutdown that will not deadlock."""
    # threading._shutdown can deadlock forever
    # see https://github.com/justengel/continuous_threading#shutdown-update
    # for additional detail
    remaining_threads = [
        thread
        for thread in threading.enumerate()
        if thread is not threading.main_thread()
        and not thread.daemon
        and thread.is_alive()
    ]

    if not remaining_threads:
        return

    timeout_per_thread = THREADING_SHUTDOWN_TIMEOUT / len(remaining_threads)
    for thread in remaining_threads:
        try:
            thread.join(timeout_per_thread)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to join thread: %s", err)