async def exchange_code_for_tokens(
        self,
        code: str,
        scopes: list[str],
        code_verifier: Optional[str],
    ) -> OAuth2Credentials:
        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if code_verifier:
            data["code_verifier"] = code_verifier
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
                f"Token exchange failed: {tokens.get('error_description', tokens['error'])}"
            )

        if "access_token" not in tokens:
            raise RuntimeError("OAuth token response missing 'access_token' field")

        now = int(time.time())
        expires_in = tokens.get("expires_in")

        return OAuth2Credentials(
            provider=self.PROVIDER_NAME,
            title=None,
            access_token=SecretStr(tokens["access_token"]),
            refresh_token=(
                SecretStr(tokens["refresh_token"])
                if tokens.get("refresh_token")
                else None
            ),
            access_token_expires_at=now + expires_in if expires_in else None,
            refresh_token_expires_at=None,
            scopes=scopes,
            metadata={
                "mcp_token_url": self.token_url,
                "mcp_resource_url": self.resource_url,
            },
        )