async def async_create_refresh_token(
        self,
        user: models.User,
        client_id: str | None = None,
        client_name: str | None = None,
        client_icon: str | None = None,
        token_type: str | None = None,
        access_token_expiration: timedelta = ACCESS_TOKEN_EXPIRATION,
        credential: models.Credentials | None = None,
    ) -> models.RefreshToken:
        """Create a new refresh token for a user."""
        if not user.is_active:
            raise ValueError("User is not active")

        if user.system_generated and client_id is not None:
            raise ValueError(
                "System generated users cannot have refresh tokens connected "
                "to a client."
            )

        if token_type is None:
            if user.system_generated:
                token_type = models.TOKEN_TYPE_SYSTEM
            else:
                token_type = models.TOKEN_TYPE_NORMAL

        if token_type is models.TOKEN_TYPE_NORMAL:
            expire_at = time.time() + REFRESH_TOKEN_EXPIRATION
        else:
            expire_at = None

        if user.system_generated != (token_type == models.TOKEN_TYPE_SYSTEM):
            raise ValueError(
                "System generated users can only have system type refresh tokens"
            )

        if token_type == models.TOKEN_TYPE_NORMAL and client_id is None:
            raise ValueError("Client is required to generate a refresh token.")

        if (
            token_type == models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
            and client_name is None
        ):
            raise ValueError("Client_name is required for long-lived access token")

        if token_type == models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN:
            for token in user.refresh_tokens.values():
                if (
                    token.client_name == client_name
                    and token.token_type == models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
                ):
                    # Each client_name can only have one
                    # long_lived_access_token type of refresh token
                    raise ValueError(f"{client_name} already exists")

        return await self._store.async_create_refresh_token(
            user,
            client_id,
            client_name,
            client_icon,
            token_type,
            access_token_expiration,
            expire_at,
            credential,
        )