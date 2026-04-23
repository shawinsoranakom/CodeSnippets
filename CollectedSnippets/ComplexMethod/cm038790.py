def split_zmq_path(path: str) -> tuple[str, str, str]:
    """Split a zmq path into its parts."""
    parsed = parse_url(path)
    if not parsed.scheme:
        raise ValueError(f"Invalid zmq path: {path}")

    scheme = parsed.scheme
    host = parsed.hostname or ""
    port = "" if parsed.port is None else str(parsed.port)
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]  # Remove brackets for IPv6 address

    if scheme == "tcp" and not all((host, port)):
        # The host and port fields are required for tcp
        raise ValueError(f"Invalid zmq path: {path}")

    if scheme != "tcp" and port:
        # port only makes sense with tcp
        raise ValueError(f"Invalid zmq path: {path}")

    return scheme, host, port