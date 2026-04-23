async def _refresh_tokens(
        self, credentials: OAuth2Credentials
    ) -> OAuth2Credentials:
        """
        Added for completeness, as WordPress tokens don't expire
        """

        logger.debug("Attempting to refresh OAuth tokens")

        # Server-side tokens don't expire
        if credentials.access_token_expires_at is None:
            logger.info("Token does not expire (server-side token), no refresh needed")
            return credentials

        if credentials.refresh_token is None:
            logger.error("Cannot refresh tokens - no refresh token available")
            raise ValueError("No refresh token available")

        try:
            response: OAuthTokenResponse = await oauth_refresh_tokens(
                client_id=self.client_id,
                client_secret=self.client_secret if self.client_secret else "",
                refresh_token=credentials.refresh_token.get_secret_value(),
            )
            logger.info("Successfully refreshed tokens")

            # Preserve blog info from original credentials
            metadata = credentials.metadata or {}
            if response.blog_id:
                metadata["blog_id"] = response.blog_id
            if response.blog_url:
                metadata["blog_url"] = response.blog_url

            new_credentials = OAuth2Credentials(
                access_token=SecretStr(response.access_token),
                refresh_token=(
                    SecretStr(response.refresh_token)
                    if response.refresh_token
                    else credentials.refresh_token
                ),
                access_token_expires_at=(
                    int(time.time()) + response.expires_in
                    if response.expires_in
                    else None
                ),
                refresh_token_expires_at=None,
                provider=self.PROVIDER_NAME,
                scopes=credentials.scopes,
                metadata=metadata,
            )

            if response.expires_in:
                logger.debug(
                    f"New access token expires in {response.expires_in} seconds"
                )
            else:
                logger.debug("New token does not expire")

            return new_credentials

        except Exception as e:
            logger.error(f"Failed to refresh tokens: {str(e)}")
            raise