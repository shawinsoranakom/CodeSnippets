def wait_for_server_ready(host, port, protocol) -> None:
    """Wait for the server to become ready by polling the health endpoint."""
    # Use localhost for health check when host is 0.0.0.0 (bind to all interfaces)
    health_check_host = "localhost" if host == "0.0.0.0" else host  # noqa: S104

    status_code = 0
    while status_code != httpx.codes.OK:
        # If the server process died (e.g. database version check failed), stop waiting.
        if process_manager.webapp_process and not process_manager.webapp_process.is_alive():
            sys.exit(process_manager.webapp_process.exitcode or 1)
        try:
            status_code = httpx.get(
                f"{protocol}://{health_check_host}:{port}/health",
                verify=health_check_host not in ("127.0.0.1", "localhost"),
            ).status_code
        except HTTPError:
            time.sleep(1)
        except Exception:  # noqa: BLE001
            logger.debug("Error while waiting for the server to become ready.", exc_info=True)
            time.sleep(1)