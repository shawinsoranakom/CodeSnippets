async def get_async_requests_session(**kwargs) -> ClientSession:
    """Get an aiohttp session object with the applied user settings or environment variables."""
    # pylint: disable=import-outside-toplevel
    import aiohttp  # noqa
    import atexit
    import ssl

    # If a session is already provided, just return it.
    if "session" in kwargs and isinstance(kwargs.get("session"), ClientSession):
        return kwargs["session"]
    # Handle SSL settings and proxies
    # We will accommodate the Requests environment variable for the CA bundle and HTTP Proxies, if provided.
    # The settings file will take precedence over the environment variables.
    python_settings = get_python_request_settings()
    _ = kwargs.pop("raise_for_status", None)

    proxy = python_settings.get("proxy")
    http_proxy = os.environ.get("HTTP_PROXY", os.environ.get("HTTPS_PROXY"))
    https_proxy = os.environ.get("HTTPS_PROXY", os.environ.get("HTTP_PROXY"))

    # aiohttp will attempt to upgrade the proxy to https.
    if not proxy and http_proxy is not None and http_proxy == https_proxy:
        python_settings["proxy"] = http_proxy.replace("https:", "http:")

    # If a proxy is provided, or verify_ssl is False, we don't need to handle the certificate and create SSL context.
    # This takes priority over the cafile.
    if python_settings.get("proxy") or python_settings.get("verify_ssl") is False:
        python_settings["verify_ssl"] = None
        python_settings["ssl"] = False
    elif (
        python_settings.get("certfile")
        or python_settings.get("cafile")
        or os.environ.get("REQUESTS_CA_BUNDLE")
    ):
        ca = python_settings.get("cafile") or os.environ.get("REQUESTS_CA_BUNDLE")
        cert = python_settings.get("certfile")
        key = python_settings.get("keyfile")
        password = python_settings.get("password")
        ssl_context = ssl.create_default_context()

        if ca:
            ssl_context.load_verify_locations(cafile=ca)

        if cert:
            ssl_context.load_cert_chain(
                certfile=cert,
                keyfile=key,
                password=password,
            )

        python_settings["ssl"] = ssl_context

    ssl_kwargs = {
        k: v
        for k, v in python_settings.items()
        if k in ["ssl", "verify_ssl", "fingerprint"] and v is not None
    }

    # Merge the updated python_settings dict with the kwargs.
    if python_settings:
        kwargs.update(
            {k: v for k, v in python_settings.items() if not k.endswith("file")}
        )

    # SSL settings get passed to the TCPConnector used by the session.
    connector = kwargs.pop("connector", None) or (
        aiohttp.TCPConnector(ttl_dns_cache=300, **ssl_kwargs) if ssl_kwargs else None
    )

    conn_kwargs = {"connector": connector} if connector else {}

    # Add basic auth for proxies, if provided.
    p_auth = kwargs.pop("proxy_auth", [])
    if p_auth:
        conn_kwargs["proxy_auth"] = aiohttp.BasicAuth(
            *p_auth if isinstance(p_auth, (list, tuple)) else p_auth
        )
    # Add basic auth for server, if provided.
    s_auth = kwargs.pop("auth", [])
    if s_auth:
        conn_kwargs["auth"] = aiohttp.BasicAuth(
            *s_auth if isinstance(s_auth, (list, tuple)) else s_auth
        )
    # Add cookies to the session, if provided.
    _cookies = kwargs.pop("cookies", None)
    if _cookies:
        if isinstance(_cookies, dict):
            conn_kwargs["cookies"] = _cookies
        elif isinstance(_cookies, aiohttp.CookieJar):
            conn_kwargs["cookie_jar"] = _cookies

    # Pass any remaining kwargs to the session
    for k, v in kwargs.items():
        if v is None:
            continue
        if k == "timeout":
            conn_kwargs["timeout"] = (
                v
                if isinstance(v, aiohttp.ClientTimeout)
                else aiohttp.ClientTimeout(total=v)
            )
        elif k not in ("ssl", "verify_ssl", "fingerprint") and k in python_settings:
            conn_kwargs[k] = v

    _session: ClientSession = ClientSession(**conn_kwargs)

    def at_exit(session):
        """Close the session at exit if it was orphaned."""
        if not session.closed:
            run_async(session.close)

    # Register the session to close at exit
    atexit.register(at_exit, _session)

    return _session