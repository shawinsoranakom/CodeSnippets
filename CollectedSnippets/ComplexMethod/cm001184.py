async def token(
    request: TokenRequestByCode | TokenRequestByRefreshToken = Body(),
) -> TokenResponse:
    """
    OAuth 2.0 Token Endpoint

    Exchanges authorization code or refresh token for access token.

    Grant Types:
    1. authorization_code: Exchange authorization code for tokens
       - Required: grant_type, code, redirect_uri, client_id, client_secret
       - Optional: code_verifier (required if PKCE was used)

    2. refresh_token: Exchange refresh token for new access token
       - Required: grant_type, refresh_token, client_id, client_secret

    Returns:
    - access_token: Bearer token for API access (1 hour TTL)
    - token_type: "Bearer"
    - expires_in: Seconds until access token expires
    - refresh_token: Token for refreshing access (30 days TTL)
    - scopes: List of scopes
    """
    # Validate client credentials
    try:
        app = await validate_client_credentials(
            request.client_id, request.client_secret
        )
    except InvalidClientError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Handle authorization_code grant
    if request.grant_type == "authorization_code":
        # Consume authorization code
        try:
            user_id, scopes = await consume_authorization_code(
                code=request.code,
                application_id=app.id,
                redirect_uri=request.redirect_uri,
                code_verifier=request.code_verifier,
            )
        except InvalidGrantError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # Create access and refresh tokens
        access_token = await create_access_token(app.id, user_id, scopes)
        refresh_token = await create_refresh_token(app.id, user_id, scopes)

        logger.info(
            f"Access token issued for user #{user_id} and app {app.name} (#{app.id})"
            "via authorization code"
        )

        if not access_token.token or not refresh_token.token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate tokens",
            )

        return TokenResponse(
            token_type="Bearer",
            access_token=access_token.token.get_secret_value(),
            access_token_expires_at=access_token.expires_at,
            refresh_token=refresh_token.token.get_secret_value(),
            refresh_token_expires_at=refresh_token.expires_at,
            scopes=list(s.value for s in scopes),
        )

    # Handle refresh_token grant
    elif request.grant_type == "refresh_token":
        # Refresh access token
        try:
            new_access_token, new_refresh_token = await refresh_tokens(
                request.refresh_token, app.id
            )
        except InvalidGrantError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        logger.info(
            f"Tokens refreshed for user #{new_access_token.user_id} "
            f"by app {app.name} (#{app.id})"
        )

        if not new_access_token.token or not new_refresh_token.token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate tokens",
            )

        return TokenResponse(
            token_type="Bearer",
            access_token=new_access_token.token.get_secret_value(),
            access_token_expires_at=new_access_token.expires_at,
            refresh_token=new_refresh_token.token.get_secret_value(),
            refresh_token_expires_at=new_refresh_token.expires_at,
            scopes=list(s.value for s in new_access_token.scopes),
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant_type: {request.grant_type}. "
            "Must be 'authorization_code' or 'refresh_token'",
        )