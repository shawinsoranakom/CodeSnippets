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