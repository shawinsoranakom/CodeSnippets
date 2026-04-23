async def validate(
        self,
        conversation_id: str,
        cookies_str: str,
        authorization_header: str | None = None,
    ) -> str | None:
        """
        Validate the conversation access using either an API key from the Authorization header
        or a keycloak_auth cookie.

        Args:
            conversation_id: The ID of the conversation
            cookies_str: The cookies string from the request
            authorization_header: The Authorization header from the request, if available

        Returns:
            A tuple of (user_id, github_user_id)

        Raises:
            ConnectionRefusedError: If the user does not have access to the conversation
            AuthError: If the authentication fails
            RuntimeError: If there is an error with the configuration or user info
        """
        # Try to authenticate using Authorization header first
        if authorization_header and authorization_header.startswith('Bearer '):
            api_key = authorization_header.replace('Bearer ', '')
            user_id = await self._validate_api_key(api_key)

            if user_id:
                logger.info(
                    f'User {user_id} is connecting to conversation {conversation_id} via API key'
                )

                await self._validate_conversation_access(conversation_id, user_id)
                return user_id

        # Fall back to cookie authentication
        token_manager = TokenManager()
        config = load_openhands_config()
        cookies = (
            dict(cookie.split('=', 1) for cookie in cookies_str.split('; '))
            if cookies_str
            else {}
        )

        signed_token = cookies.get('keycloak_auth', '')
        if not signed_token:
            logger.warning('No keycloak_auth cookie or valid Authorization header')
            raise ConnectionRefusedError(
                'No keycloak_auth cookie or valid Authorization header'
            )
        if not config.jwt_secret:
            raise RuntimeError('JWT secret not found')

        try:
            user_auth = await saas_user_auth_from_signed_token(signed_token)
            access_token = await user_auth.get_access_token()
        except ExpiredError:
            raise ConnectionRefusedError('SESSION$TIMEOUT_MESSAGE')
        if access_token is None:
            raise AuthError('no_access_token')
        user_info = await token_manager.get_user_info(access_token.get_secret_value())
        # sub is a required field in KeycloakUserInfo, validation happens in get_user_info
        user_id = user_info.sub

        logger.info(f'User {user_id} is connecting to conversation {conversation_id}')

        await self._validate_conversation_access(conversation_id, user_id)  # type: ignore
        return user_id