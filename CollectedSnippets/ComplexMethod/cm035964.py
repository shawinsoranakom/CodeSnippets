async def load_tokens(
        self,
        check_expiration_and_refresh: Callable[
            [ProviderType, str, int, int], Awaitable[Dict[str, str | int] | None]
        ]
        | None = None,
    ) -> Dict[str, str | int] | None:
        """Load authentication tokens from the database and refresh them if necessary.

        This method uses a double-checked locking pattern to minimize lock contention:
        1. First, check if the token is valid WITHOUT acquiring a lock (fast path)
        2. If refresh is needed, acquire a lock with a timeout
        3. Double-check if refresh is still needed (another request may have refreshed)
        4. Perform the refresh if still needed

        The row-level lock ensures that only one refresh operation is performed per
        refresh token, which is important because most IDPs invalidate the old refresh
        token after it's used once.

        Args:
            check_expiration_and_refresh: A function that checks if the tokens have
                expired and attempts to refresh them. It should return a dictionary
                containing the new access_token, refresh_token, and their respective
                expiration timestamps. If no refresh is needed, it should return None.

        Returns:
            A dictionary containing the access_token, refresh_token,
            access_token_expires_at, and refresh_token_expires_at.
            If no token record is found, returns None.

        Raises:
            TokenRefreshError: If the lock cannot be acquired within the timeout
                period. This typically means another request is holding the lock
                for an extended period. Callers should handle this by returning
                a 401 response to prompt the user to re-authenticate.
        """
        # FAST PATH: Check without lock first to avoid unnecessary lock contention
        async with a_session_maker() as session:
            result = await session.execute(
                select(AuthTokens).filter(
                    AuthTokens.keycloak_user_id == self.keycloak_user_id,
                    AuthTokens.identity_provider == self.identity_provider_value,
                )
            )
            token_record = result.scalars().one_or_none()

            if not token_record:
                return None

            # Check if token needs refresh
            access_expired, _ = self._is_token_expired(
                token_record.access_token_expires_at,
                token_record.refresh_token_expires_at,
            )

            # If token is still valid, return it without acquiring a lock
            if not access_expired or check_expiration_and_refresh is None:
                return {
                    'access_token': token_record.access_token,
                    'refresh_token': token_record.refresh_token,
                    'access_token_expires_at': token_record.access_token_expires_at,
                    'refresh_token_expires_at': token_record.refresh_token_expires_at,
                }

        # SLOW PATH: Token needs refresh, acquire lock
        try:
            async with a_session_maker() as session:
                async with session.begin():
                    # Set a lock timeout to prevent indefinite blocking
                    # This ensures we don't hold connections forever if something goes wrong
                    await session.execute(
                        text(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT_SECONDS}s'")
                    )

                    # Acquire row-level lock to prevent concurrent refresh attempts
                    result = await session.execute(
                        select(AuthTokens)
                        .filter(
                            AuthTokens.keycloak_user_id == self.keycloak_user_id,
                            AuthTokens.identity_provider
                            == self.identity_provider_value,
                        )
                        .with_for_update()
                    )
                    token_record = result.scalars().one_or_none()

                    if not token_record:
                        return None

                    # Double-check: another request may have refreshed while we waited for the lock
                    access_expired, _ = self._is_token_expired(
                        token_record.access_token_expires_at,
                        token_record.refresh_token_expires_at,
                    )

                    if not access_expired:
                        # Token was refreshed by another request while we waited
                        logger.debug(
                            'Token was refreshed by another request while waiting for lock'
                        )
                        return {
                            'access_token': token_record.access_token,
                            'refresh_token': token_record.refresh_token,
                            'access_token_expires_at': token_record.access_token_expires_at,
                            'refresh_token_expires_at': token_record.refresh_token_expires_at,
                        }

                    # We're the one doing the refresh
                    token_refresh = await check_expiration_and_refresh(
                        self.idp,
                        token_record.refresh_token,
                        token_record.access_token_expires_at,
                        token_record.refresh_token_expires_at,
                    )

                    if token_refresh:
                        await session.execute(
                            update(AuthTokens)
                            .where(AuthTokens.id == token_record.id)
                            .values(
                                access_token=token_refresh['access_token'],
                                refresh_token=token_refresh['refresh_token'],
                                access_token_expires_at=token_refresh[
                                    'access_token_expires_at'
                                ],
                                refresh_token_expires_at=token_refresh[
                                    'refresh_token_expires_at'
                                ],
                            )
                        )
                        await session.commit()

                    return (
                        token_refresh
                        if token_refresh
                        else {
                            'access_token': token_record.access_token,
                            'refresh_token': token_record.refresh_token,
                            'access_token_expires_at': token_record.access_token_expires_at,
                            'refresh_token_expires_at': token_record.refresh_token_expires_at,
                        }
                    )
        except OperationalError as e:
            # Lock timeout - another request is holding the lock for too long
            logger.warning(
                f'Token refresh lock timeout for user {self.keycloak_user_id}: {e}'
            )
            raise TokenRefreshError(
                'Unable to refresh token due to lock timeout. Please try again.'
            ) from e