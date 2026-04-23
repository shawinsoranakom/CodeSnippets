def _is_port_available(self, port: int, host: str = "localhost") -> bool:
        """Check if a port is available by trying to bind to it.

        Args:
            port: Port number to check
            host: Host to check (default: localhost)

        Returns:
            True if port is available (not in use), False if in use

        Raises:
            ValueError: If port is not in valid range (0-65535)
        """
        import errno

        # Validate port range before attempting bind
        max_port = 65535
        if not isinstance(port, int) or port < 0 or port > max_port:
            msg = f"Invalid port number: {port}. Port must be between 0 and {max_port}."
            raise ValueError(msg)

        # Check both IPv4 and IPv6 to ensure port is truly available
        # MCP Composer tries to bind on both, so we need to check both

        # Check IPv4
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Don't use SO_REUSEADDR here as it can give false positives
                sock.bind((host, port))
        except OSError:
            return False  # Port is in use on IPv4

        # Check IPv6 (if supported on this system)
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
                # Don't use SO_REUSEADDR here as it can give false positives
                # Use ::1 for localhost on IPv6
                ipv6_host = "::1" if host in ("localhost", "127.0.0.1") else host
                sock.bind((ipv6_host, port))
        except OSError as e:
            # Check if it's "address already in use" error
            # errno.EADDRINUSE is 48 on macOS, 98 on Linux, 10048 on Windows (WSAEADDRINUSE)
            # We check both the standard errno and Windows-specific error code
            if e.errno in (errno.EADDRINUSE, 10048):
                return False  # Port is in use on IPv6
            # For other errors (e.g., IPv6 not supported, EADDRNOTAVAIL), continue
            # IPv6 might not be supported on this system, which is okay

        return True