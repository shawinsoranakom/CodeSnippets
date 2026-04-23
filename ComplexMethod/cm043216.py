def from_string(proxy_str: str) -> "ProxyConfig":
        """Create a ProxyConfig from a string.

        Supported formats:
        - 'http://username:password@ip:port'
        - 'http://ip:port'
        - 'socks5://ip:port'
        - 'ip:port:username:password'
        - 'ip:port'
        """
        s = (proxy_str or "").strip()
        # URL with credentials
        if "@" in s and "://" in s:
            auth_part, server_part = s.split("@", 1)
            protocol, credentials = auth_part.split("://", 1)
            if ":" in credentials:
                username, password = credentials.split(":", 1)
                return ProxyConfig(
                    server=f"{protocol}://{server_part}",
                    username=username,
                    password=password,
                )
        # URL without credentials (keep scheme)
        if "://" in s and "@" not in s:
            return ProxyConfig(server=s)
        # Colon separated forms
        parts = s.split(":")
        if len(parts) == 4:
            ip, port, username, password = parts
            return ProxyConfig(server=f"http://{ip}:{port}", username=username, password=password)
        if len(parts) == 2:
            ip, port = parts
            return ProxyConfig(server=f"http://{ip}:{port}")
        raise ValueError(f"Invalid proxy string format: {proxy_str}")