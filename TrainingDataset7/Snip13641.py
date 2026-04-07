def generic(
        self,
        method,
        path,
        data="",
        content_type="application/octet-stream",
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        """Construct an arbitrary HTTP request."""
        parsed = urlsplit(str(path))  # path can be lazy
        data = force_bytes(data, settings.DEFAULT_CHARSET)
        r = {
            "PATH_INFO": self._get_path(parsed),
            "REQUEST_METHOD": method,
            "SERVER_PORT": "443" if secure else "80",
            "wsgi.url_scheme": "https" if secure else "http",
        }
        if data:
            r.update(
                {
                    "CONTENT_LENGTH": str(len(data)),
                    "CONTENT_TYPE": content_type,
                    "wsgi.input": FakePayload(data),
                }
            )
        if headers:
            extra.update(HttpHeaders.to_wsgi_names(headers))
        if query_params:
            extra["QUERY_STRING"] = urlencode(query_params, doseq=True)
        r.update(extra)
        # If QUERY_STRING is absent or empty, extract it from the URL.
        if not r.get("QUERY_STRING"):
            # WSGI requires latin-1 encoded strings. See get_path_info().
            r["QUERY_STRING"] = parsed.query.encode().decode("iso-8859-1")
        return self.request(**r)