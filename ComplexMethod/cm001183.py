async def authorize(
    request: AuthorizeRequest = Body(),
    user_id: str = Security(get_user_id),
) -> AuthorizeResponse:
    """
    OAuth 2.0 Authorization Endpoint

    User must be logged in (authenticated with Supabase JWT).
    This endpoint creates an authorization code and returns a redirect URL.

    PKCE (Proof Key for Code Exchange) is REQUIRED for all authorization requests.

    The frontend consent screen should call this endpoint after the user approves,
    then redirect the user to the returned `redirect_url`.

    Request Body:
    - client_id: The OAuth application's client ID
    - redirect_uri: Where to redirect after authorization (must match registered URI)
    - scopes: List of permissions (e.g., "EXECUTE_GRAPH READ_GRAPH")
    - state: Anti-CSRF token provided by client (will be returned in redirect)
    - response_type: Must be "code" (for authorization code flow)
    - code_challenge: PKCE code challenge (required)
    - code_challenge_method: "S256" (recommended) or "plain"

    Returns:
    - redirect_url: The URL to redirect the user to (includes authorization code)

    Error cases return a redirect_url with error parameters, or raise HTTPException
    for critical errors (like invalid redirect_uri).
    """
    try:
        # Validate response_type
        if request.response_type != "code":
            return _error_redirect_url(
                request.redirect_uri,
                request.state,
                "unsupported_response_type",
                "Only 'code' response type is supported",
            )

        # Get application
        app = await get_oauth_application(request.client_id)
        if not app:
            return _error_redirect_url(
                request.redirect_uri,
                request.state,
                "invalid_client",
                "Unknown client_id",
            )

        if not app.is_active:
            return _error_redirect_url(
                request.redirect_uri,
                request.state,
                "invalid_client",
                "Application is not active",
            )

        # Validate redirect URI
        if not validate_redirect_uri(app, request.redirect_uri):
            # For invalid redirect_uri, we can't redirect safely
            # Must return error instead
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid redirect_uri. "
                    f"Must be one of: {', '.join(app.redirect_uris)}"
                ),
            )

        # Parse and validate scopes
        try:
            requested_scopes = [APIKeyPermission(s.strip()) for s in request.scopes]
        except ValueError as e:
            return _error_redirect_url(
                request.redirect_uri,
                request.state,
                "invalid_scope",
                f"Invalid scope: {e}",
            )

        if not requested_scopes:
            return _error_redirect_url(
                request.redirect_uri,
                request.state,
                "invalid_scope",
                "At least one scope is required",
            )

        if not validate_scopes(app, requested_scopes):
            return _error_redirect_url(
                request.redirect_uri,
                request.state,
                "invalid_scope",
                "Application is not authorized for all requested scopes. "
                f"Allowed: {', '.join(s.value for s in app.scopes)}",
            )

        # Create authorization code
        auth_code = await create_authorization_code(
            application_id=app.id,
            user_id=user_id,
            scopes=requested_scopes,
            redirect_uri=request.redirect_uri,
            code_challenge=request.code_challenge,
            code_challenge_method=request.code_challenge_method,
        )

        # Build redirect URL with authorization code
        params = {
            "code": auth_code.code,
            "state": request.state,
        }
        redirect_url = f"{request.redirect_uri}?{urlencode(params)}"

        logger.info(
            f"Authorization code issued for user #{user_id} "
            f"and app {app.name} (#{app.id})"
        )

        return AuthorizeResponse(redirect_url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in authorization endpoint: {e}", exc_info=True)
        return _error_redirect_url(
            request.redirect_uri,
            request.state,
            "server_error",
            "An unexpected error occurred",
        )