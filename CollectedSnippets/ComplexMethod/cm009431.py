async def validate_url(url: str, policy: SSRFPolicy = SSRFPolicy()) -> None:
    """Validate a URL against the SSRF policy, including DNS resolution.

    This is the primary entry-point for async code paths. It delegates
    scheme/hostname/allowed-hosts checks to `validate_url_sync`, then
    resolves DNS and validates every resolved IP.

    Raises:
        SSRFBlockedError: If the URL violates the policy.
    """
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""

    validate_url_sync(url, policy)

    allowed = {h.lower() for h in _effective_allowed_hosts(policy)}
    if hostname.lower() in allowed:
        return

    scheme = (parsed.scheme or "").lower()
    port = parsed.port or (443 if scheme == "https" else 80)
    try:
        addrinfo = await asyncio.to_thread(
            socket.getaddrinfo, hostname, port, type=socket.SOCK_STREAM
        )
    except socket.gaierror as exc:
        msg = "DNS resolution failed"
        raise SSRFBlockedError(msg) from exc

    for _family, _type, _proto, _canonname, sockaddr in addrinfo:
        validate_resolved_ip(str(sockaddr[0]), policy)