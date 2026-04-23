def _build_auth_kwargs(self) -> dict[str, Any]:
        """Build authentication configuration for OpenSearch client.

        Constructs the appropriate authentication parameters based on the
        selected auth mode (basic username/password or JWT token).

        Returns:
            Dictionary containing authentication configuration

        Raises:
            ValueError: If required authentication parameters are missing
        """
        mode = (self.auth_mode or "basic").strip().lower()
        if mode == "jwt":
            token = (self.jwt_token or "").strip()
            if not token:
                msg = "Auth Mode is 'jwt' but no jwt_token was provided."
                raise ValueError(msg)
            header_name = (self.jwt_header or "Authorization").strip()
            header_value = f"Bearer {token}" if self.bearer_prefix else token
            return {"headers": {header_name: header_value}}
        user = (self.username or "").strip()
        pwd = (self.password or "").strip()
        if not user or not pwd:
            msg = "Auth Mode is 'basic' but username/password are missing."
            raise ValueError(msg)
        return {"http_auth": (user, pwd)}