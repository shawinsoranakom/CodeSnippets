async def consume_authorization_code(
    code: str,
    application_id: str,
    redirect_uri: str,
    code_verifier: Optional[str] = None,
) -> tuple[str, list[APIPermission]]:
    """
    Consume an authorization code and return (user_id, scopes).

    This marks the code as used and validates:
    - Code exists and matches application
    - Code is not expired
    - Code has not been used
    - Redirect URI matches
    - PKCE code verifier matches (if code challenge was provided)

    Raises:
        InvalidGrantError: If code is invalid, expired, used, or PKCE fails
    """
    auth_code = await PrismaOAuthAuthorizationCode.prisma().find_unique(
        where={"code": code}
    )

    if not auth_code:
        raise InvalidGrantError("authorization code not found")

    # Validate application
    if auth_code.applicationId != application_id:
        raise InvalidGrantError(
            "authorization code does not belong to this application"
        )

    # Check if already used
    if auth_code.usedAt is not None:
        raise InvalidGrantError(
            f"authorization code already used at {auth_code.usedAt}"
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    if auth_code.expiresAt < now:
        raise InvalidGrantError("authorization code expired")

    # Validate redirect URI
    if auth_code.redirectUri != redirect_uri:
        raise InvalidGrantError("redirect_uri mismatch")

    # Validate PKCE if code challenge was provided
    if auth_code.codeChallenge:
        if not code_verifier:
            raise InvalidGrantError("code_verifier required but not provided")

        if not _verify_pkce(
            code_verifier, auth_code.codeChallenge, auth_code.codeChallengeMethod
        ):
            raise InvalidGrantError("PKCE verification failed")

    # Mark code as used
    await PrismaOAuthAuthorizationCode.prisma().update(
        where={"code": code},
        data={"usedAt": now},
    )

    return auth_code.userId, [APIPermission(s) for s in auth_code.scopes]