async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(injectable_session_scope),
) -> User | None:
    """Resolve the current user if authenticated, otherwise return None.

    Checks HttpOnly cookie (access_token_lf), Authorization header, and API key.
    Used by endpoints that support both authenticated and unauthenticated access.
    """
    token = request.cookies.get("access_token_lf")
    api_key = request.query_params.get("x-api-key") or request.headers.get("x-api-key")
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = token or auth_header[len("Bearer ") :]

    if not token and not api_key:
        return None

    try:
        return await _auth_service().get_current_user_for_sse(token, api_key, db)
    except (AuthenticationError, HTTPException):
        return None