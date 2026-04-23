def decode_netloc(self) -> str:
        """Decodes the netloc part into a string."""
        host = self.host or ""

        if isinstance(host, bytes):
            host = host.decode()

        rv = _decode_idna(host)

        if ":" in rv:
            rv = f"[{rv}]"
        port = self.port
        if port is not None:
            rv = f"{rv}:{port}"
        auth = ":".join(
            filter(
                None,
                [
                    _url_unquote_legacy(self.raw_username or "", "/:%@"),
                    _url_unquote_legacy(self.raw_password or "", "/:%@"),
                ],
            )
        )
        if auth:
            rv = f"{auth}@{rv}"
        return rv