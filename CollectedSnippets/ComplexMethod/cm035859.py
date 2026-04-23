async def get_provider_tokens(self) -> PROVIDER_TOKEN_TYPE | None:
        logger.debug('saas_user_auth_get_provider_tokens')
        if self.provider_tokens is not None:
            return self.provider_tokens
        provider_tokens = {}
        access_token = await self.get_access_token()
        if not access_token:
            raise AuthError()

        user_secrets = await self.get_secrets()

        try:
            # TODO: I think we can do this in a single request if we refactor
            async with a_session_maker() as session:
                result = await session.execute(
                    select(AuthTokens).where(
                        AuthTokens.keycloak_user_id == self.user_id
                    )
                )
                tokens = result.scalars().all()

            for token in tokens:
                idp_type = ProviderType(token.identity_provider)
                try:
                    host = None
                    if user_secrets and idp_type in user_secrets.provider_tokens:
                        host = user_secrets.provider_tokens[idp_type].host

                    if idp_type == ProviderType.BITBUCKET_DATA_CENTER and not host:
                        host = BITBUCKET_DATA_CENTER_HOST or None

                    provider_token = await token_manager.get_idp_token(
                        access_token.get_secret_value(),
                        idp=idp_type,
                    )
                    # TODO: Currently we don't store the IDP user id in our refresh table. We should.
                    provider_tokens[idp_type] = ProviderToken(
                        token=SecretStr(provider_token), user_id=None, host=host
                    )
                except Exception as e:
                    # If there was a problem with a refresh token we log and delete it
                    logger.error(
                        f'Error refreshing provider_token token: {e}',
                        extra={
                            'user_id': self.user_id,
                            'idp_type': token.identity_provider,
                        },
                    )
                    async with a_session_maker() as session:
                        await session.execute(
                            delete(AuthTokens).where(AuthTokens.id == token.id)
                        )
                        await session.commit()
                    raise

            self.provider_tokens = MappingProxyType(provider_tokens)
            return self.provider_tokens
        except Exception as e:
            # Any error refreshing tokens means we need to log in again
            raise AuthError() from e