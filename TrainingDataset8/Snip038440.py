def start_listening(app: tornado.web.Application) -> None:
    """Makes the server start listening at the configured port.

    In case the port is already taken it tries listening to the next available
    port.  It will error after MAX_PORT_SEARCH_RETRIES attempts.

    """

    http_server = HTTPServer(
        app, max_buffer_size=config.get_option("server.maxUploadSize") * 1024 * 1024
    )

    if server_address_is_unix_socket():
        start_listening_unix_socket(http_server)
    else:
        start_listening_tcp_socket(http_server)