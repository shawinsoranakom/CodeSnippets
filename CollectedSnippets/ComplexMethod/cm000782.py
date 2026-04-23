async def discover_auth_server_metadata(
        self, auth_server_url: str
    ) -> dict[str, Any] | None:
        """Fetch the OAuth Authorization Server Metadata (RFC 8414).

        Given an authorization server URL, returns a dict with:
          - ``authorization_endpoint``
          - ``token_endpoint``
          - ``registration_endpoint`` (for dynamic client registration)
          - ``scopes_supported``
          - ``code_challenge_methods_supported``
          - etc.
        """
        from urllib.parse import urlparse

        parsed = urlparse(auth_server_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path.rstrip("/")

        # Try standard metadata endpoints (RFC 8414 and OpenID Connect)
        candidates = []
        if path and path != "/":
            candidates.append(f"{base}/.well-known/oauth-authorization-server{path}")
        candidates.append(f"{base}/.well-known/oauth-authorization-server")
        candidates.append(f"{base}/.well-known/openid-configuration")

        requests = Requests(
            raise_for_status=False,
        )
        for url in candidates:
            try:
                resp = await requests.get(url)
                if resp.status == 200:
                    data = resp.json()
                    if isinstance(data, dict) and "authorization_endpoint" in data:
                        return data
            except Exception:
                continue

        return None