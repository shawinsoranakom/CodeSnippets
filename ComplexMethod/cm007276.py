def get_container_host() -> str | None:
    """Get the hostname to access host services from within a container.

    Tries multiple methods to find the correct hostname:
    1. host.containers.internal (Podman) or host.docker.internal (Docker)
    2. Gateway IP from routing table (fallback for Linux)

    Returns:
        The hostname or IP to use, or None if not in a container.
    """
    # Check if we're in a container first
    container_type = detect_container_environment()
    if not container_type:
        return None

    # Try container-specific hostnames first based on detected type
    if container_type == "podman":
        # Podman: try host.containers.internal first
        try:
            socket.getaddrinfo("host.containers.internal", None)
        except socket.gaierror:
            pass
        else:
            return "host.containers.internal"

        # Fallback to host.docker.internal (for Podman Desktop on macOS)
        try:
            socket.getaddrinfo("host.docker.internal", None)
        except socket.gaierror:
            pass
        else:
            return "host.docker.internal"
    else:
        # Docker: try host.docker.internal first
        try:
            socket.getaddrinfo("host.docker.internal", None)
        except socket.gaierror:
            pass
        else:
            return "host.docker.internal"

        # Fallback to host.containers.internal (unlikely but possible)
        try:
            socket.getaddrinfo("host.containers.internal", None)
        except socket.gaierror:
            pass
        else:
            return "host.containers.internal"

    # Fallback: try to get gateway IP from routing table (Linux containers)
    try:
        with Path("/proc/net/route").open() as f:
            # Skip header
            next(f)
            for line in f:
                fields = line.strip().split()
                min_field_count = 3  # Minimum fields needed: interface, destination, gateway
                if len(fields) >= min_field_count and fields[1] == "00000000":  # Default route
                    # Gateway is in hex format (little-endian)
                    gateway_hex = fields[2]
                    # Convert little-endian hex to dotted IPv4
                    gw_int = int(gateway_hex, 16)
                    return socket.inet_ntoa(struct.pack("<L", gw_int))
    except (FileNotFoundError, PermissionError, IndexError, ValueError):
        pass

    return None