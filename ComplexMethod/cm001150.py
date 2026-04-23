async def validate_url_host(
    url: str, trusted_hostnames: Optional[list[str]] = None
) -> tuple[URL, bool, list[str]]:
    """
    Validates a (URL's) host string to prevent SSRF attacks by ensuring it does not
    point to a private, link-local, or otherwise blocked IP address — unless
    the hostname is explicitly trusted.

    Hosts in `trusted_hostnames` are permitted without checks.
    All other hosts are resolved and checked against `BLOCKED_IP_NETWORKS`.

    Params:
        url: A hostname, netloc, or URL to validate.
             If no scheme is included, `http://` is assumed.
        trusted_hostnames: A list of hostnames that don't require validation.

    Raises:
      ValueError:
        - if the URL has a disallowed URL scheme
        - if the URL/host string can't be parsed
        - if the hostname contains invalid or unsupported (non-ASCII) characters
        - if the host resolves to a blocked IP

    Returns:
        1. The validated, canonicalized, parsed host/URL,
           with hostname ASCII-safe encoding
        2. Whether the host is trusted (based on the passed `trusted_hostnames`).
        3. List of resolved IP addresses for the host; empty if the host is trusted.
    """
    parsed = parse_url(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' is not allowed; allowed schemes: "
            f"{', '.join(ALLOWED_SCHEMES)}"
        )

    if not parsed.hostname:
        raise ValueError(f"Invalid host/URL; no host in parse result: {url}")

    # IDNA encode to prevent Unicode domain attacks
    try:
        ascii_hostname = idna.encode(parsed.hostname).decode("ascii")
    except idna.IDNAError:
        raise ValueError(f"Hostname '{parsed.hostname}' has unsupported characters")

    if not HOSTNAME_REGEX.match(ascii_hostname):
        raise ValueError(f"Hostname '{parsed.hostname}' has unsupported characters")

    # Re-create parsed URL object with IDNA-encoded hostname
    parsed = URL(
        parsed.scheme,
        (ascii_hostname if parsed.port is None else f"{ascii_hostname}:{parsed.port}"),
        quote(parsed.path, safe="/%:@"),
        parsed.params,
        parsed.query,
        parsed.fragment,
    )

    is_trusted = trusted_hostnames and any(
        matches_allowed_host(parsed, allowed)
        for allowed in (
            # Normalize + parse allowlist entries the same way for consistent matching
            parse_url(w)
            for w in trusted_hostnames
        )
    )

    if is_trusted:
        return parsed, True, []

    # If not allowlisted, go ahead with host resolution and IP target check
    return parsed, False, await resolve_and_check_blocked(ascii_hostname)