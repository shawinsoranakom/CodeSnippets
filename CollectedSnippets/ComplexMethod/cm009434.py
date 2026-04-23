def handle_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        hostname = request.url.host or ""
        scheme = request.url.scheme.lower()

        validate_url_sync(str(request.url), self._policy)

        allowed = {h.lower() for h in _effective_allowed_hosts(self._policy)}
        if hostname.lower() in allowed:
            return self._inner.handle_request(request)

        port = request.url.port or (443 if scheme == "https" else 80)
        try:
            addrinfo = socket.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise SSRFBlockedError("DNS resolution failed") from exc

        if not addrinfo:
            raise SSRFBlockedError("DNS resolution returned no results")

        for _family, _type, _proto, _canonname, sockaddr in addrinfo:
            ip_str: str = sockaddr[0]  # type: ignore[assignment]
            validate_resolved_ip(ip_str, self._policy)

        pinned_ip = addrinfo[0][4][0]
        pinned_url = request.url.copy_with(host=pinned_ip)

        extensions = dict(request.extensions)
        if scheme == "https":
            extensions["sni_hostname"] = hostname.encode("ascii")

        pinned_request = httpx.Request(
            method=request.method,
            url=pinned_url,
            headers=request.headers,
            content=request.content,
            extensions=extensions,
        )

        return self._inner.handle_request(pinned_request)