async def callback(
    provider: Annotated[
        ProviderName, Path(title="The target provider for this OAuth exchange")
    ],
    code: Annotated[str, Body(title="Authorization code acquired by user login")],
    state_token: Annotated[str, Body(title="Anti-CSRF nonce")],
    user_id: Annotated[str, Security(get_user_id)],
    request: Request,
) -> CredentialsMetaResponse:
    logger.debug(f"Received OAuth callback for provider: {provider}")
    handler = _get_provider_oauth_handler(request, provider)

    # Verify the state token
    valid_state = await creds_manager.store.verify_state_token(
        user_id, state_token, provider
    )

    if not valid_state:
        logger.warning(f"Invalid or expired state token for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state token",
        )
    try:
        scopes = valid_state.scopes
        logger.debug(f"Retrieved scopes from state token: {scopes}")

        scopes = handler.handle_default_scopes(scopes)

        credentials = await handler.exchange_code_for_tokens(
            code, scopes, valid_state.code_verifier
        )

        logger.debug(f"Received credentials with final scopes: {credentials.scopes}")

        # Linear returns scopes as a single string with spaces, so we need to split them
        # TODO: make a bypass of this part of the OAuth handler
        if len(credentials.scopes) == 1 and " " in credentials.scopes[0]:
            credentials.scopes = credentials.scopes[0].split(" ")

        # Check if the granted scopes are sufficient for the requested scopes
        if not set(scopes).issubset(set(credentials.scopes)):
            # For now, we'll just log the warning and continue
            logger.warning(
                f"Granted scopes {credentials.scopes} for provider {provider.value} "
                f"do not include all requested scopes {scopes}"
            )

    except Exception as e:
        logger.error(
            f"OAuth2 Code->Token exchange failed for provider {provider.value}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth2 callback failed to exchange code for tokens: {str(e)}",
        )

    # TODO: Allow specifying `title` to set on `credentials`
    await creds_manager.create(user_id, credentials)

    logger.debug(
        f"Successfully processed OAuth callback for user {user_id} "
        f"and provider {provider.value}"
    )

    return CredentialsMetaResponse(
        id=credentials.id,
        provider=credentials.provider,
        type=credentials.type,
        title=credentials.title,
        scopes=credentials.scopes,
        username=credentials.username,
        host=(
            credentials.host if isinstance(credentials, HostScopedCredentials) else None
        ),
    )
