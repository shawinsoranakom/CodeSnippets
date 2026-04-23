def allow_cross_origin_requests():
    """True if cross-origin requests are allowed.

    We only allow cross-origin requests when CORS protection has been disabled
    with server.enableCORS=False or if using the Node server. When using the
    Node server, we have a dev and prod port, which count as two origins.

    """
    return not config.get_option("server.enableCORS") or config.get_option(
        "global.developmentMode"
    )