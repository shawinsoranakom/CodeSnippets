def is_url_from_allowed_origins(url: str) -> bool:
    """Return True if URL is from allowed origins (for CORS purpose).

    Allowed origins:
    1. localhost
    2. The internal and external IP addresses of the machine where this
       function was called from.

    If `server.enableCORS` is False, this allows all origins.
    """
    if not config.get_option("server.enableCORS"):
        # Allow everything when CORS is disabled.
        return True

    hostname = url_util.get_hostname(url)

    allowed_domains = [  # List[Union[str, Callable[[], Optional[str]]]]
        # Check localhost first.
        "localhost",
        "0.0.0.0",
        "127.0.0.1",
        # Try to avoid making unnecessary HTTP requests by checking if the user
        # manually specified a server address.
        _get_server_address_if_manually_set,
        # Then try the options that depend on HTTP requests or opening sockets.
        net_util.get_internal_ip,
        net_util.get_external_ip,
    ]

    for allowed_domain in allowed_domains:
        if callable(allowed_domain):
            allowed_domain = allowed_domain()

        if allowed_domain is None:
            continue

        if hostname == allowed_domain:
            return True

    return False