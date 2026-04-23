async def discover_auth(self) -> dict[str, Any] | None:
        """Probe the MCP server's OAuth metadata (RFC 9728 / MCP spec).

        Returns ``None`` if the server doesn't require auth, otherwise returns
        a dict with:
          - ``authorization_servers``: list of authorization server URLs
          - ``resource``: the resource indicator URL (usually the MCP endpoint)
          - ``scopes_supported``: optional list of supported scopes

        The caller can then fetch the authorization server metadata to get
        ``authorization_endpoint``, ``token_endpoint``, etc.
        """
        from urllib.parse import urlparse

        parsed = urlparse(self.server_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Build candidates for protected-resource metadata (per RFC 9728)
        path = parsed.path.rstrip("/")
        candidates = []
        if path and path != "/":
            candidates.append(f"{base}/.well-known/oauth-protected-resource{path}")
        candidates.append(f"{base}/.well-known/oauth-protected-resource")

        requests = Requests(
            raise_for_status=False,
        )
        for url in candidates:
            try:
                resp = await requests.get(url)
                if resp.status == 200:
                    data = resp.json()
                    if isinstance(data, dict) and "authorization_servers" in data:
                        return data
            except Exception:
                continue

        return None