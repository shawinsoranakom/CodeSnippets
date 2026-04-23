async def _create_user(
        client: httpx.AsyncClient,
        email: str | None,
        keycloak_user_id: str,
    ) -> bool:
        """Create a user in LiteLLM.

        Returns True if the user was created or already exists and is verified,
        False if creation failed and user does not exist.
        """
        if LITE_LLM_API_KEY is None or LITE_LLM_API_URL is None:
            logger.warning('LiteLLM API configuration not found')
            return False
        response = await client.post(
            f'{LITE_LLM_API_URL}/user/new',
            json={
                'user_email': email,
                'models': [],
                'user_id': keycloak_user_id,
                'teams': [LITE_LLM_TEAM_ID],
                'auto_create_key': False,
                'send_invite_email': False,
                'metadata': {
                    'version': ORG_SETTINGS_VERSION,
                    'model': get_default_litellm_model(),
                },
            },
        )
        if not response.is_success:
            logger.warning(
                'duplicate_user_email',
                extra={
                    'user_id': keycloak_user_id,
                    'email': email,
                },
            )
            # Litellm insists on unique email addresses - it is possible the email address was registered with a different user.
            response = await client.post(
                f'{LITE_LLM_API_URL}/user/new',
                json={
                    'user_email': None,
                    'models': [],
                    'user_id': keycloak_user_id,
                    'teams': [LITE_LLM_TEAM_ID],
                    'auto_create_key': False,
                    'send_invite_email': False,
                    'metadata': {
                        'version': ORG_SETTINGS_VERSION,
                        'model': get_default_litellm_model(),
                    },
                },
            )

            # User failed to create in litellm - this is an unforseen error state...
            if not response.is_success:
                if (
                    response.status_code in (400, 409)
                    and 'already exists' in response.text
                ):
                    logger.warning(
                        'litellm_user_already_exists',
                        extra={
                            'user_id': keycloak_user_id,
                        },
                    )
                    # Verify the user actually exists before returning success
                    user_exists = await LiteLlmManager._user_exists(
                        client, keycloak_user_id
                    )
                    if not user_exists:
                        logger.error(
                            'litellm_user_claimed_exists_but_not_found',
                            extra={
                                'user_id': keycloak_user_id,
                                'status_code': response.status_code,
                                'text': response.text,
                            },
                        )
                        return False
                    return True
                logger.error(
                    'error_creating_litellm_user',
                    extra={
                        'status_code': response.status_code,
                        'text': response.text,
                        'user_id': keycloak_user_id,
                        'email': None,
                    },
                )
                return False
            response.raise_for_status()
        return True