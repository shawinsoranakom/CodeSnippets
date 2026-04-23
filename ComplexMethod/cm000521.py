async def introspect_token(
    token: str,
    token_type_hint: Optional[Literal["access_token", "refresh_token"]] = None,
) -> TokenIntrospectionResult:
    """
    Introspect a token and return its metadata (RFC 7662).

    Returns TokenIntrospectionResult with active=True and metadata if valid,
    or active=False if the token is invalid/expired/revoked.
    """
    # Try as access token first (or if hint says "access_token")
    if token_type_hint != "refresh_token":
        try:
            token_info, app = await validate_access_token(token)
            return TokenIntrospectionResult(
                active=True,
                scopes=list(s.value for s in token_info.scopes),
                client_id=app.client_id if app else None,
                user_id=token_info.user_id,
                exp=int(token_info.expires_at.timestamp()),
                token_type="access_token",
            )
        except InvalidTokenError:
            pass  # Try as refresh token

    # Try as refresh token
    token_hash = _hash_token(token)
    refresh_token = await PrismaOAuthRefreshToken.prisma().find_unique(
        where={"token": token_hash}
    )

    if refresh_token and refresh_token.revokedAt is None:
        # Check if valid (not expired)
        now = datetime.now(timezone.utc)
        if refresh_token.expiresAt > now:
            app = await get_oauth_application_by_id(refresh_token.applicationId)
            return TokenIntrospectionResult(
                active=True,
                scopes=list(s for s in refresh_token.scopes),
                client_id=app.client_id if app else None,
                user_id=refresh_token.userId,
                exp=int(refresh_token.expiresAt.timestamp()),
                token_type="refresh_token",
            )

    # Token not found or inactive
    return TokenIntrospectionResult(active=False)