async def install_callback(
    request: Request, code: str = '', state: str = '', error: str = ''
):
    """Callback from slack authentication. Verifies, then forwards into keycloak authentication."""
    if not code or error:
        logger.warning(
            'slack_install_callback_error',
            extra={
                'code': code,
                'state': state,
                'error': error,
            },
        )
        return _html_response(
            title='Error',
            description=html.escape(error or 'No code provided'),
            status_code=400,
        )

    if not config.jwt_secret:
        logger.error('slack_install_callback_error JWT not configured.')
        return _html_response(
            title='Error',
            description=html.escape('JWT not configured'),
            status_code=500,
        )

    try:
        client = AsyncWebClient()  # no prepared token needed for this
        # Complete the installation by calling oauth.v2.access API method
        oauth_response = await client.oauth_v2_access(
            client_id=SLACK_CLIENT_ID,
            client_secret=SLACK_CLIENT_SECRET,
            redirect_uri=f'https://{request.url.netloc}{request.url.path}',
            code=code,
        )
        bot_access_token = oauth_response.get('access_token')
        team_id = oauth_response.get('team', {}).get('id')
        authed_user = oauth_response.get('authed_user') or {}

        # Create a state variable for keycloak oauth
        payload = {}
        if state:
            payload = jwt.decode(
                state, config.jwt_secret.get_secret_value(), algorithms=['HS256']
            )
        payload['slack_user_id'] = authed_user.get('id')
        payload['bot_access_token'] = bot_access_token
        payload['team_id'] = team_id

        state = jwt.encode(
            payload, config.jwt_secret.get_secret_value(), algorithm='HS256'
        )

        # Redirect into keycloak
        scope = quote('openid email profile offline_access')
        redirect_uri = f'{HOST_URL}/slack/keycloak-callback'
        auth_url = (
            f'{KEYCLOAK_SERVER_URL_EXT}/realms/{KEYCLOAK_REALM_NAME}/protocol/openid-connect/auth'
            f'?client_id={KEYCLOAK_CLIENT_ID}&response_type=code'
            f'&redirect_uri={redirect_uri}'
            f'&scope={scope}'
            f'&state={state}'
        )

        return RedirectResponse(auth_url)
    except Exception:  # type: ignore
        logger.error('unexpected_error', exc_info=True, stack_info=True)
        return _html_response(
            title='Error',
            description='Internal server Error',
            status_code=500,
        )