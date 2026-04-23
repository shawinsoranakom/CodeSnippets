def validate_safe_url(
    url: str | AnyHttpUrl,
    *,
    allow_private: bool = False,
    allow_http: bool = True,
) -> str:
    """Validate a URL for SSRF protection.

    This function validates URLs to prevent Server-Side Request Forgery (SSRF) attacks
    by blocking requests to private networks and cloud metadata endpoints.

    Args:
        url: The URL to validate (string or Pydantic HttpUrl).
        allow_private: If `True`, allows private IPs and localhost (for development).
                      Cloud metadata endpoints are ALWAYS blocked.
        allow_http: If `True`, allows both HTTP and HTTPS.  If `False`, only HTTPS.

    Returns:
        The validated URL as a string.

    Raises:
        ValueError: If URL is invalid or potentially dangerous.
    """
    url_str = str(url)
    parsed = urlparse(url_str)
    hostname = parsed.hostname or ""

    # Test-environment bypass (preserved from original implementation)
    if (
        os.environ.get("LANGCHAIN_ENV") == "local_test"
        and hostname.startswith("test")
        and "server" in hostname
    ):
        return url_str

    policy = _policy_for(allow_private=allow_private, allow_http=allow_http)

    # Synchronous scheme + hostname checks
    try:
        _validate_url_sync(url_str, policy)
    except SSRFBlockedError as exc:
        raise ValueError(str(exc)) from exc

    # DNS resolution and IP validation
    try:
        addr_info = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            socket.AF_UNSPEC,
            socket.SOCK_STREAM,
        )

        for result in addr_info:
            ip_str: str = result[4][0]  # type: ignore[assignment]
            try:
                _validate_resolved_ip(ip_str, policy)
            except SSRFBlockedError as exc:
                raise ValueError(str(exc)) from exc

    except socket.gaierror as e:
        msg = f"Failed to resolve hostname '{hostname}': {e}"
        raise ValueError(msg) from e
    except OSError as e:
        msg = f"Network error while validating URL: {e}"
        raise ValueError(msg) from e

    return url_str