def _set_connection_attributes(self, request):
        proxy = request.meta.get("proxy")
        if proxy:
            proxy_parsed = urlparse(to_bytes(proxy, encoding="ascii"))
            self.scheme = proxy_parsed.scheme
            self.host = proxy_parsed.hostname
            self.port = proxy_parsed.port
            self.netloc = proxy_parsed.netloc
            if self.port is None:
                self.port = 443 if proxy_parsed.scheme == b"https" else 80
            self.path = self.url
        else:
            parsed = urlparse_cached(request)
            path_str = urlunparse(
                ("", "", parsed.path or "/", parsed.params, parsed.query, "")
            )
            self.path = to_bytes(path_str, encoding="ascii")
            assert parsed.hostname is not None
            self.host = to_bytes(parsed.hostname, encoding="ascii")
            self.port = parsed.port
            self.scheme = to_bytes(parsed.scheme, encoding="ascii")
            self.netloc = to_bytes(parsed.netloc, encoding="ascii")
            if self.port is None:
                self.port = 443 if self.scheme == b"https" else 80