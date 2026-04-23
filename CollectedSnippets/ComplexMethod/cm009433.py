async def handle_async_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        hostname = request.url.host or ""
        scheme = request.url.scheme.lower()

        # 1-3. Scheme, hostname, and pattern checks (reuse sync validator).
        try:
            validate_url_sync(str(request.url), self._policy)
        except SSRFBlockedError:
            raise

        # Allowed-hosts bypass - skip DNS/IP validation entirely.
        allowed = {h.lower() for h in _effective_allowed_hosts(self._policy)}
        if hostname.lower() in allowed:
            return await self._inner.handle_async_request(request)

        # 4. DNS resolution
        port = request.url.port or (443 if scheme == "https" else 80)
        try:
            addrinfo = await asyncio.to_thread(
                socket.getaddrinfo,
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise SSRFBlockedError("DNS resolution failed") from exc

        if not addrinfo:
            raise SSRFBlockedError("DNS resolution returned no results")

        # 5. Validate ALL resolved IPs - any blocked means reject.
        for _family, _type, _proto, _canonname, sockaddr in addrinfo:
            ip_str: str = sockaddr[0]  # type: ignore[assignment]
            validate_resolved_ip(ip_str, self._policy)

        # 6. Pin to first resolved IP.
        pinned_ip = addrinfo[0][4][0]

        # 7. Rewrite URL to use pinned IP, preserving Host header and SNI.
        pinned_url = request.url.copy_with(host=pinned_ip)

        # Build extensions dict, adding sni_hostname for HTTPS so TLS
        # certificate validation uses the original hostname.
        extensions = dict(request.extensions)
        if scheme == "https":
            extensions["sni_hostname"] = hostname.encode("ascii")

        pinned_request = httpx.Request(
            method=request.method,
            url=pinned_url,
            headers=request.headers,  # Host header already set to original
            content=request.content,
            extensions=extensions,
        )

        return await self._inner.handle_async_request(pinned_request)