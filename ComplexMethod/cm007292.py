def validate_url_for_ssrf(url: str, *, warn_only: bool = True) -> None:
    """Validate a URL to prevent SSRF attacks.

    This function performs the following checks:
    1. Validates the URL scheme (only http/https allowed)
    2. Validates hostname exists
    3. Checks if hostname/IP is in allowlist
    4. If direct IP: validates it's not in blocked ranges
    5. If hostname: resolves to IPs and validates they're not in blocked ranges

    Args:
        url: URL to validate
        warn_only: If True, only log warnings instead of raising errors (default: True)
            TODO: Change default to False in next major version (2.0)

    Raises:
        SSRFProtectionError: If the URL is blocked due to SSRF protection (only if warn_only=False)
        ValueError: If the URL is malformed
    """
    # Skip validation if SSRF protection is disabled
    if not is_ssrf_protection_enabled():
        return

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        msg = f"Invalid URL format: {e}"
        raise ValueError(msg) from e

    try:
        # Validate scheme
        _validate_url_scheme(parsed.scheme)
        if parsed.scheme not in ("http", "https"):
            return

        # Validate hostname exists
        hostname = _validate_hostname_exists(parsed.hostname)

        # Check if hostname/IP is in allowlist (early return if allowed)
        if is_host_allowed(hostname):
            logger.debug("Hostname %s is in allowlist, bypassing SSRF checks", hostname)
            return

        # Validate direct IP address or resolve hostname
        is_direct_ip = _validate_direct_ip_address(hostname)
        if is_direct_ip:
            # Direct IP was handled (allowed or exception raised)
            return

        # Not a direct IP, resolve hostname and validate
        _validate_hostname_resolution(hostname)
    except SSRFProtectionError as e:
        if warn_only:
            logger.warning("SSRF Protection Warning: %s [URL: %s]", str(e), url)
            logger.warning(
                "This request will be blocked when SSRF protection is enforced in the next major version. "
                "Please review your API Request components."
            )
            return
        raise