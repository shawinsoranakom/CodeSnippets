def _get_pid_on_port(port: int) -> "tuple[int, str] | None":
    """Return (pid, process_name) of the process listening on *port*, or None.

    Uses psutil when available.  Falls back gracefully to None so callers
    can still report the port conflict without process details.

    Works on Windows, macOS, and Linux wherever psutil is installed.
    """
    try:
        import psutil
    except ImportError:
        return None
    try:
        for conn in psutil.net_connections(kind = "tcp"):
            if conn.status == "LISTEN" and conn.laddr.port == port:
                if conn.pid is None:
                    return None
                try:
                    proc = psutil.Process(conn.pid)
                    return (conn.pid, proc.name())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return (conn.pid, "<unknown>")
    except (psutil.AccessDenied, OSError) as e:
        # psutil.net_connections() needs elevated privileges on some platforms
        logger.debug("Failed to scan network connections for port %s: %s", port, e)
    return None