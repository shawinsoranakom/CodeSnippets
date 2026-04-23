def _browser_server_port() -> int:
    """Port where users should point their browsers in order to connect to the
    app.

    This is used to:
    - Set the correct URL for CORS and XSRF protection purposes.
    - Show the URL on the terminal
    - Open the browser

    Default: whatever value is set in server.port.
    """
    return int(get_option("server.port"))