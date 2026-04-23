def get_requests_session(**kwargs) -> "Session":
    """Get a requests session object with the applied user settings or environment variables."""
    # pylint: disable=import-outside-toplevel
    import requests

    # If a session is already provided, just return it.
    if "session" in kwargs and isinstance(kwargs.get("session"), requests.Session):
        return kwargs["session"]

    # We want to add a user agent to the request, so check if there are any headers
    # If there are headers, check if there is a user agent, if not add one.
    # Some requests seem to work only with a specific user agent, so we want to be able to override it.
    python_settings = get_python_request_settings()
    headers = kwargs.pop("headers", {})
    headers.update(python_settings.pop("headers", {}))

    if "User-Agent" not in headers:
        headers["User-Agent"] = get_user_agent()

    # Allow a custom session for caching, if desired
    _session: requests.Session = kwargs.pop("session", None) or requests.Session()
    _session.headers.update(headers)

    if python_settings.get("verify_ssl") is False:
        _session.verify = False
    else:
        ca_file = python_settings.get("cafile")
        requests_ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE")
        cert = ca_file or requests_ca_bundle
        if cert:
            bundle = requests_ca_bundle if requests_ca_bundle != cert else None
            _session.verify = combine_certificates(cert, bundle)

    if certfile := python_settings.get("certfile"):
        keyfile = python_settings.get("keyfile")
        _session.cert = (certfile, keyfile) if keyfile else certfile

    proxy = python_settings.get("proxy")
    http_proxy = os.environ.get("HTTP_PROXY", os.environ.get("HTTPS_PROXY"))
    https_proxy = os.environ.get("HTTPS_PROXY", os.environ.get("HTTP_PROXY"))

    if http_proxy is not None and http_proxy == https_proxy:
        https_proxy = None

    if http_proxy or https_proxy or proxy:
        proxies: dict = {}
        if http := http_proxy or https_proxy or proxy:
            proxies["http"] = http
        if https := https_proxy or http_proxy or proxy:
            proxies["https"] = https
        _session.proxies = proxies

    if cookies := python_settings.get("cookies"):
        _session.cookies = (
            cookies
            if isinstance(cookies, requests.cookies.RequestsCookieJar)  # type: ignore
            else requests.cookies.cookiejar_from_dict(cookies)  # type: ignore
        )

    if auth := python_settings.get("auth"):
        _session.auth = auth if isinstance(auth, (tuple, requests.auth.AuthBase)) else tuple(auth)  # type: ignore

    if kwargs:
        for key, value in kwargs.items():
            try:
                if hasattr(_session, key):
                    if hasattr(getattr(_session, key, None), "update"):
                        getattr(_session, key, {}).update(value)
                    else:
                        setattr(_session, key, value)
            except AttributeError:
                continue

    _session.trust_env = False

    return _session