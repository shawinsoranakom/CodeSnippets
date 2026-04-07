def __init__(
        self,
        enforce_csrf_checks=False,
        raise_request_exception=True,
        *,
        headers=None,
        query_params=None,
        **defaults,
    ):
        super().__init__(headers=headers, query_params=query_params, **defaults)
        self.handler = ClientHandler(enforce_csrf_checks)
        self.raise_request_exception = raise_request_exception
        self.exc_info = None
        self.extra = None
        self.headers = None