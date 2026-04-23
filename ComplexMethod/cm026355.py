def _parse_client_id(client_id: str) -> ParseResult:
    """Test if client id is a valid URL according to IndieAuth section 3.2.

    https://indieauth.spec.indieweb.org/#client-identifier
    """
    parts = _parse_url(client_id)

    # Client identifier URLs
    # MUST have either an https or http scheme
    if parts.scheme not in ("http", "https"):
        raise ValueError

    # MUST contain a path component
    # Handled by url canonicalization.

    # MUST NOT contain single-dot or double-dot path segments
    if any(segment in (".", "..") for segment in parts.path.split("/")):
        raise ValueError(
            "Client ID cannot contain single-dot or double-dot path segments"
        )

    # MUST NOT contain a fragment component
    if parts.fragment != "":
        raise ValueError("Client ID cannot contain a fragment")

    # MUST NOT contain a username or password component
    if parts.username is not None:
        raise ValueError("Client ID cannot contain username")

    if parts.password is not None:
        raise ValueError("Client ID cannot contain password")

    # MAY contain a port
    try:
        # parts raises ValueError when port cannot be parsed as int
        _ = parts.port
    except ValueError as ex:
        raise ValueError("Client ID contains invalid port") from ex

    # Additionally, hostnames
    # MUST be domain names or a loopback interface and
    # MUST NOT be IPv4 or IPv6 addresses except for IPv4 127.0.0.1
    # or IPv6 [::1]

    # We are not goint to follow the spec here. We are going to allow
    # any internal network IP to be used inside a client id.

    address = None

    try:
        netloc = parts.netloc

        # Strip the [, ] from ipv6 addresses before parsing
        if netloc[0] == "[" and netloc[-1] == "]":
            netloc = netloc[1:-1]

        address = ip_address(netloc)
    except ValueError:
        # Not an ip address
        pass

    if address is None or is_local(address):
        return parts

    raise ValueError("Hostname should be a domain name or local IP address")