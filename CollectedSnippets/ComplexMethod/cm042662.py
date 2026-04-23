def from_args(
        self,
        headers: Mapping[bytes, bytes] | None = None,
        url: str | None = None,
        filename: str | None = None,
        body: bytes | None = None,
    ) -> type[Response]:
        """Guess the most appropriate Response class based on
        the given arguments."""
        cls = Response
        if headers is not None:
            cls = self.from_headers(headers)
        if cls is Response and url is not None:
            cls = self.from_filename(url)
        if cls is Response and filename is not None:
            cls = self.from_filename(filename)
        if cls is Response and body is not None:
            cls = self.from_body(body)
        return cls