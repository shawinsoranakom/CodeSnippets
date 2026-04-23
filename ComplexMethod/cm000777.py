async def exchange_code_for_tokens(
        self, code: str, scopes: list[str], code_verifier: Optional[str] = None
    ) -> OAuth2Credentials:
        logger.debug("Exchanging authorization code for tokens")
        logger.debug(f"Code: {code[:4]}...")
        logger.debug(f"Scopes: {scopes}")

        # WordPress doesn't use PKCE, so code_verifier is not needed

        try:
            response: OAuthTokenResponse = await oauth_exchange_code_for_tokens(
                client_id=self.client_id,
                client_secret=self.client_secret if self.client_secret else "",
                code=code,
                redirect_uri=self.redirect_uri,
            )
            logger.info("Successfully exchanged code for tokens")

            # Store blog info in metadata
            metadata = {}
            if response.blog_id:
                metadata["blog_id"] = response.blog_id
            if response.blog_url:
                metadata["blog_url"] = response.blog_url

            # WordPress tokens from code flow don't expire
            credentials = OAuth2Credentials(
                access_token=SecretStr(response.access_token),
                refresh_token=(
                    SecretStr(response.refresh_token)
                    if response.refresh_token
                    else None
                ),
                access_token_expires_at=None,
                refresh_token_expires_at=None,
                provider=self.PROVIDER_NAME,
                scopes=scopes if scopes else [],
                metadata=metadata,
            )

            if response.expires_in:
                logger.debug(
                    f"Token expires in {response.expires_in} seconds (client-side token)"
                )
            else:
                logger.debug("Token does not expire (server-side token)")

            return credentials

        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {str(e)}")
            raise