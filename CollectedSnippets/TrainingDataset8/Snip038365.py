def _on_server_start(server: Server) -> None:
    _maybe_print_old_git_warning(server.main_script_path)
    _print_url(server.is_running_hello)
    report_watchdog_availability()
    _print_new_version_message()

    # Load secrets.toml if it exists. If the file doesn't exist, this
    # function will return without raising an exception. We catch any parse
    # errors and display them here.
    try:
        secrets.load_if_toml_exists()
    except Exception as ex:
        LOGGER.error(f"Failed to load secrets.toml file", exc_info=ex)

    def maybe_open_browser():
        if config.get_option("server.headless"):
            # Don't open browser when in headless mode.
            return

        if server.browser_is_connected:
            # Don't auto-open browser if there's already a browser connected.
            # This can happen if there's an old tab repeatedly trying to
            # connect, and it happens to success before we launch the browser.
            return

        if config.is_manually_set("browser.serverAddress"):
            addr = config.get_option("browser.serverAddress")
        elif config.is_manually_set("server.address"):
            if server_address_is_unix_socket():
                # Don't open browser when server address is an unix socket
                return
            addr = config.get_option("server.address")
        else:
            addr = "localhost"

        util.open_browser(server_util.get_url(addr))

    # Schedule the browser to open on the main thread, but only if no other
    # browser connects within 1s.
    asyncio.get_running_loop().call_later(BROWSER_WAIT_TIMEOUT_SEC, maybe_open_browser)