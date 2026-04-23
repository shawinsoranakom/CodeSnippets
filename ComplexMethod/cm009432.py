def validate_url_sync(url: str, policy: SSRFPolicy = SSRFPolicy()) -> None:
    """Synchronous URL validation (no DNS resolution).

    Suitable for Pydantic validators and other sync contexts. Checks scheme
    and hostname patterns only - use `validate_url` for full DNS-aware checking.

    Raises:
        SSRFBlockedError: If the URL violates the policy.
    """
    parsed = urllib.parse.urlparse(url)

    scheme = (parsed.scheme or "").lower()
    if scheme not in policy.allowed_schemes:
        msg = f"scheme '{scheme}' not allowed"
        raise SSRFBlockedError(msg)

    hostname = parsed.hostname
    if not hostname:
        msg = "missing hostname"
        raise SSRFBlockedError(msg)

    allowed = _effective_allowed_hosts(policy)
    if hostname.lower() in {h.lower() for h in allowed}:
        return

    try:
        ipaddress.ip_address(hostname)
        validate_resolved_ip(hostname, policy)
    except SSRFBlockedError:
        raise
    except ValueError:
        pass
    else:
        return

    validate_hostname(hostname, policy)