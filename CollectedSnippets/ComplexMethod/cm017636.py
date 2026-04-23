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
        parsed = urlsplit(str(path))  # path can be lazy.
        data = force_bytes(data, settings.DEFAULT_CHARSET)
        s = {
            "method": method,
            "path": self._get_path(parsed),
            "server": ("127.0.0.1", "443" if secure else "80"),
            "scheme": "https" if secure else "http",
            "headers": [(b"host", b"testserver")],
        }
        if self.defaults:
            extra = {**self.defaults, **extra}
        if data:
            s["headers"].extend(
                [
                    (b"content-length", str(len(data)).encode("ascii")),
                    (b"content-type", content_type.encode("ascii")),
                ]
            )
            s["_body_file"] = FakePayload(data)
        if query_params:
            s["query_string"] = urlencode(query_params, doseq=True)
        elif query_string := extra.pop("QUERY_STRING", None):
            s["query_string"] = query_string
        else:
            # If QUERY_STRING is absent or empty, we want to extract it from
            # the URL.
            s["query_string"] = parsed.query
        if headers:
            extra.update(HttpHeaders.to_asgi_names(headers))
        s["headers"] += [
            # Avoid breaking test clients that just want to supply normalized
            # ASGI names, regardless of the fact that ASGIRequest drops headers
            # with underscores (CVE-2026-3902).
            (key.lower().replace("_", "-").encode("ascii"), value.encode("latin1"))
            for key, value in extra.items()
        ]
        return self.request(**s)