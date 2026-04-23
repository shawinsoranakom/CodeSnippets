def build_record(
        self,
        *,
        response: httpx.Response | None = None,
        error: BaseException | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        total_ms = (time.perf_counter() - self.started_at) * 1000
        url = self.request.url
        host = url.host or ""
        port = url.port
        default_port = {"http": 80, "https": 443}.get(url.scheme)
        host_display = host if port in (None, default_port) else f"{host}:{port}"

        http_version = None
        status_code = None
        bytes_downloaded = None
        response_complete = False
        if response is not None:
            status_code = response.status_code
            response_complete = response.is_closed
            raw_http_version = response.extensions.get("http_version")
            if isinstance(raw_http_version, bytes):
                http_version = raw_http_version.decode("ascii", errors="replace")
            elif raw_http_version is not None:
                http_version = str(raw_http_version)

            if response_complete:
                try:
                    bytes_downloaded = len(response.content)
                except httpx.ResponseNotRead:
                    pass

        return {
            "method": self.request.method,
            "scheme": url.scheme,
            "host": host,
            "host_display": host_display,
            "port": port,
            "path": url.path,
            "has_query": bool(url.query),
            "url": f"{url.scheme}://{host_display}{url.path}{'?...' if url.query else ''}",
            "request_id": self.request.headers.get("x-amzn-trace-id") or self.request.headers.get("x-request-id"),
            "status_code": status_code,
            "http_version": http_version,
            "bytes_downloaded": bytes_downloaded,
            "total_ms": total_ms,
            "stream": stream,
            "response_complete": response_complete,
            "phases_ms": dict(sorted(self.phases_ms.items())),
            "error": None if error is None else f"{type(error).__name__}: {error}",
        }