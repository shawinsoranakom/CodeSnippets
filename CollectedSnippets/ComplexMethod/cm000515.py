def matches_url(self, url: str) -> bool:
        """Check if this credential should be applied to the given URL."""

        request_host, request_port = _extract_host_from_url(url)
        cred_scope_host, cred_scope_port = _extract_host_from_url(self.host)
        if not request_host:
            return False

        # If a port is specified in credential host, the request host port must match
        if cred_scope_port is not None and request_port != cred_scope_port:
            return False
        # Non-standard ports are only allowed if explicitly specified in credential host
        elif cred_scope_port is None and request_port not in (80, 443, None):
            return False

        # Simple host matching
        if cred_scope_host == request_host:
            return True

        # Support wildcard matching (e.g., "*.example.com" matches "api.example.com")
        if cred_scope_host.startswith("*."):
            domain = cred_scope_host[2:]  # Remove "*."
            return request_host.endswith(f".{domain}") or request_host == domain

        return False