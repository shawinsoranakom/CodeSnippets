def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        url: str | None = None,
        timeout: int | None = 90,
        additional_headers: dict | None = None,
    ):
        err = "Either (`host` and `port`) or `url` must be provided, but not both."
        if url is not None:
            if host is not None or port is not None:
                raise ValueError(err)
            self.url = url
        else:
            if host is None:
                raise ValueError(err)
            port = port or 80

            protocol = "https" if port == 443 else "http"
            self.url = f"{protocol}://{host}:{port}"

        self.timeout = timeout
        self.additional_headers = additional_headers or {}

        self.index_client = DocumentStoreClient(
            url=self.url,
            timeout=self.timeout,
            additional_headers=self.additional_headers,
        )