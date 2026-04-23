async def _authenticate_with_token(self, token: str, db: AsyncSession) -> User:
        """Internal method to authenticate with token (raises generic exceptions)."""
        from langflow.services.auth.utils import ACCESS_TOKEN_TYPE, get_jwt_verification_key

        settings_service = self.settings
        algorithm = settings_service.auth_settings.ALGORITHM
        verification_key = get_jwt_verification_key(settings_service)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                payload = jwt.decode(token, verification_key, algorithms=[algorithm])
            user_id: UUID = payload.get("sub")  # type: ignore[assignment]
            token_type: str = payload.get("type")  # type: ignore[assignment]

            # Validate token type
            if token_type != ACCESS_TOKEN_TYPE:
                logger.error(f"Token type is invalid: {token_type}. Expected: {ACCESS_TOKEN_TYPE}.")
                msg = "Invalid token type"
                raise AuthInvalidTokenError(msg)

            # Check expiration
            if expires := payload.get("exp", None):
                expires_datetime = datetime.fromtimestamp(expires, timezone.utc)
                if datetime.now(timezone.utc) > expires_datetime:
                    logger.info("Token expired for user")
                    msg = "Token has expired"
                    raise TokenExpiredError(msg)

            # Validate payload
            if user_id is None or token_type is None:
                logger.info(f"Invalid token payload. Token type: {token_type}")
                msg = "Invalid token payload"
                raise AuthInvalidTokenError(msg)

        except (TokenExpiredError, AuthInvalidTokenError):
            raise
        except jwt.ExpiredSignatureError as e:
            logger.info("Token signature has expired")
            msg = "Token has expired"
            raise TokenExpiredError(msg) from e
        except InvalidTokenError as e:
            logger.debug("JWT validation failed: Invalid token format or signature")
            msg = "Invalid token"
            raise AuthInvalidTokenError(msg) from e
        except Exception as e:
            logger.error(f"Unexpected error decoding token: {e}")
            msg = "Token validation failed"
            raise AuthInvalidTokenError(msg) from e

        # Get user from database
        user = await get_user_by_id(db, user_id)
        if user is None:
            logger.info("User not found")
            msg = "User not found"
            raise InvalidCredentialsError(msg)

        if not user.is_active:
            logger.info("User is inactive")
            msg = "User account is inactive"
            raise InactiveUserError(msg)

        return user