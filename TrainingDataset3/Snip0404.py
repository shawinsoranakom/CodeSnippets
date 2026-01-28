async def require_auth(
    api_key: str | None = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_auth),
) -> APIAuthorizationInfo:
    """
    Unified authentication middleware supporting both API keys and OAuth tokens.

    Supports two authentication methods, which are checked in order:
    1. X-API-Key header (existing API key authentication)
    2. Authorization: Bearer <token> header (OAuth access token)

    Returns:
        APIAuthorizationInfo: base class of both APIKeyInfo and OAuthAccessTokenInfo.
    """
    # Try API key first
    if api_key is not None:
        api_key_info = await validate_api_key(api_key)
        if api_key_info:
            return api_key_info
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    # Try OAuth bearer token
    if bearer is not None:
        try:
            token_info, _ = await validate_access_token(bearer.credentials)
            return token_info
        except (InvalidClientError, InvalidTokenError) as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # No credentials provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication. Provide API key or access token.",
    )
