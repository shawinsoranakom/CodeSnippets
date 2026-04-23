async def _refresh_tokens(
        self, credentials: OAuth2Credentials
    ) -> OAuth2Credentials:
        if not credentials.refresh_token:
            raise ValueError("No refresh token available for MCP OAuth credentials")

        data: dict[str, str] = {
            "grant_type": "refresh_token",
            "refresh_token": credentials.refresh_token.get_secret_value(),
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if self.resource_url:
            data["resource"] = self.resource_url

        response = await Requests(raise_for_status=True).post(
            self.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        tokens = response.json()

        if "error" in tokens:
            raise RuntimeError(
                f"Token refresh failed: {tokens.get('error_description', tokens['error'])}"
            )

        if "access_token" not in tokens:
            raise RuntimeError("OAuth refresh response missing 'access_token' field")

        now = int(time.time())
        expires_in = tokens.get("expires_in")

        return OAuth2Credentials(
            id=credentials.id,
            provider=self.PROVIDER_NAME,
            title=credentials.title,
            access_token=SecretStr(tokens["access_token"]),
            refresh_token=(
                SecretStr(tokens["refresh_token"])
                if tokens.get("refresh_token")
                else credentials.refresh_token
            ),
            access_token_expires_at=now + expires_in if expires_in else None,
            refresh_token_expires_at=credentials.refresh_token_expires_at,
            scopes=credentials.scopes,
            metadata=credentials.metadata,
        )