def __init__(
        self,
        headers=None,
        timeout: int = None,
        connector: BaseConnector = None,
        proxy: str = None,
        proxies=None,
        impersonate = None,
        **kwargs
    ):
        if proxies is None:
            proxies = {}
        if headers is None:
            headers = {}
        if impersonate:
            headers = {
                **DEFAULT_HEADERS,
                **headers
            }
        if not has_brotli and "br" in headers.get("accept-encoding", ""):
            headers["accept-encoding"] = "gzip, deflate"
        connect = None
        if isinstance(timeout, tuple):
            connect, timeout = timeout
        if timeout is not None:
            timeout = ClientTimeout(timeout, connect)
        if proxy is None:
            proxy = proxies.get("all", proxies.get("https"))
        self.inner = ClientSession(
            **kwargs,
            timeout=timeout,
            response_class=StreamResponse,
            connector=get_connector(connector, proxy),
            headers=headers
        )