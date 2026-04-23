async def keycloak_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    code: str = '',
    state: str = '',
    error: str = '',
):
    if not code or error:
        logger.warning(
            'problem_retrieving_keycloak_tokens',
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
        logger.error('problem_retrieving_keycloak_tokens JWT not configured.')
        return _html_response(
            title='Error',
            description=html.escape('JWT not configured'),
            status_code=500,
        )

    payload: dict[str, str] = jwt.decode(
        state, config.jwt_secret.get_secret_value(), algorithms=['HS256']
    )
    slack_user_id = payload['slack_user_id']
    bot_access_token: str | None = payload['bot_access_token']
    team_id = payload['team_id']

    # Retrieve the keycloak_user_id
    redirect_uri = f'{HOST_URL}{request.url.path}'
    (
        keycloak_access_token,
        keycloak_refresh_token,
    ) = await token_manager.get_keycloak_tokens(code, redirect_uri)
    if not keycloak_access_token or not keycloak_refresh_token:
        logger.warning(
            'problem_retrieving_keycloak_tokens',
            extra={
                'code': code,
                'state': state,
                'error': error,
            },
        )
        return _html_response(
            title='Failed to authenticate.',
            description=f'Please re-login into <a href="{HOST_URL}" style="color:#ecedee;text-decoration:underline;">OpenHands Cloud</a>. Then try <a href="https://docs.all-hands.dev/usage/cloud/slack-installation" style="color:#ecedee;text-decoration:underline;">installing the OpenHands Slack App</a> again',
            status_code=400,
        )

    user_info = await token_manager.get_user_info(keycloak_access_token)
    keycloak_user_id = user_info.sub
    user = await UserStore.get_user_by_id(keycloak_user_id)
    if not user:
        return _html_response(
            title='Failed to authenticate.',
            description=f'Please re-login into <a href="{HOST_URL}" style="color:#ecedee;text-decoration:underline;">OpenHands Cloud</a>. Then try <a href="https://docs.all-hands.dev/usage/cloud/slack-installation" style="color:#ecedee;text-decoration:underline;">installing the OpenHands Slack App</a> again',
            status_code=400,
        )

    # These tokens are offline access tokens - store them!
    await token_manager.store_offline_token(keycloak_user_id, keycloak_refresh_token)

    idp: str = user_info.identity_provider or ProviderType.GITHUB.value
    idp_type = 'oidc'
    if ':' in idp:
        idp, idp_type = idp.rsplit(':', 1)
        idp_type = idp_type.lower()
    await token_manager.store_idp_tokens(
        ProviderType(idp), keycloak_user_id, keycloak_access_token
    )

    # Retrieve bot token
    if team_id and bot_access_token:
        await slack_team_store.create_team(team_id, bot_access_token)
    else:
        bot_access_token = await slack_team_store.get_team_bot_token(team_id)

    if not bot_access_token:
        logger.error(
            f'Account linking failed, did not find slack team {team_id} for user {keycloak_user_id}'
        )
        return

    # Retrieve the display_name from slack
    client = AsyncWebClient(token=bot_access_token)
    slack_user_info = await client.users_info(user=slack_user_id)
    slack_display_name = slack_user_info.data['user']['profile']['display_name']
    slack_user = SlackUser(
        keycloak_user_id=keycloak_user_id,
        org_id=user.current_org_id,
        slack_user_id=slack_user_id,
        slack_display_name=slack_display_name,
    )

    async with a_session_maker(expire_on_commit=False) as session:
        # First delete any existing tokens
        await session.execute(
            delete(SlackUser).where(SlackUser.slack_user_id == slack_user_id)
        )

        # Store the token
        session.add(slack_user)
        await session.commit()

    message = Message(source=SourceType.SLACK, message=payload)

    background_tasks.add_task(slack_manager.receive_message, message)
    return _html_response(
        title='OpenHands Authentication Successful!',
        description='It is now safe to close this tab.',
        status_code=200,
    )