async def authenticate_with_credentials(
        self,
        token: str | None,
        api_key: str | None,
        db: AsyncSession,
    ) -> User | UserRead:
        """Framework-agnostic authentication method.

        This is the core authentication logic that validates credentials and returns a user.


        Args:
            token: Access token (JWT, OIDC token, etc.)
            api_key: API key for authentication
            db: Database session


        Returns:
            User or UserRead object


        Raises:
            MissingCredentialsError: If no credentials provided
            InvalidCredentialsError: If credentials are invalid
            InvalidTokenError: If token format/signature is invalid
            TokenExpiredError: If token has expired
            InactiveUserError: If user account is inactive
        """
        # Try token authentication first (if token provided)
        if token:
            try:
                return await self._authenticate_with_token(token, db)
            except (AuthInvalidTokenError, TokenExpiredError, InactiveUserError):
                # Re-raise our generic exceptions
                raise
            except Exception as e:
                # Token auth failed; fall back to API key if provided
                if api_key:
                    try:
                        user = await self._authenticate_with_api_key(api_key, db)
                        if user:
                            return user
                        msg = "Invalid API key"
                        raise InvalidCredentialsError(msg)
                    except InvalidCredentialsError:
                        raise
                    except Exception as api_key_err:
                        logger.error(f"Unexpected error during API key authentication: {api_key_err}")
                        msg = "API key authentication failed"
                        raise InvalidCredentialsError(msg) from api_key_err
                logger.error(f"Unexpected error during token authentication: {e}")
                msg = "Token authentication failed"
                raise AuthInvalidTokenError(msg) from e

        # Try API key authentication
        if api_key:
            try:
                user = await self._authenticate_with_api_key(api_key, db)
                if user:
                    return user
                msg = "Invalid API key"
                raise InvalidCredentialsError(msg)
            except InvalidCredentialsError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error during API key authentication: {e}")
                msg = "API key authentication failed"
                raise InvalidCredentialsError(msg) from e

        # No credentials provided
        msg = "No authentication credentials provided"
        raise MissingCredentialsError(msg)