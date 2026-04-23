def __init__(
        self, content_type=None, status=None, reason=None, charset=None, headers=None
    ):
        self.headers = ResponseHeaders(headers)
        self._charset = charset
        if "Content-Type" not in self.headers:
            if content_type is None:
                content_type = f"text/html; charset={self.charset}"
            self.headers["Content-Type"] = content_type
        elif content_type:
            raise ValueError(
                "'headers' must not contain 'Content-Type' when the "
                "'content_type' parameter is provided."
            )
        self._resource_closers = []
        # This parameter is set by the handler. It's necessary to preserve the
        # historical behavior of request_finished.
        self._handler_class = None
        self.cookies = SimpleCookie()
        self.closed = False
        if status is not None:
            try:
                self.status_code = int(status)
            except (ValueError, TypeError):
                raise TypeError("HTTP status code must be an integer.")

            if not 100 <= self.status_code <= 599:
                raise ValueError("HTTP status code must be an integer from 100 to 599.")
        self._reason_phrase = reason