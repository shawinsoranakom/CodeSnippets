def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = fastapi.Security(
        optional_bearer
    ),
) -> str | None:
    """
    Attempts to extract the user ID ("sub" claim) from a Bearer JWT if provided.

    This dependency allows for both authenticated and anonymous access. If a valid bearer token is
    supplied, it parses the JWT and extracts the user ID. If the token is missing or invalid, it returns None,
    treating the request as anonymous.

    Args:
        credentials: Optional HTTPAuthorizationCredentials object from FastAPI Security dependency.

    Returns:
        The user ID (str) extracted from the JWT "sub" claim, or None if no valid token is present.
    """
    if not credentials:
        return None

    try:
        # Parse JWT token to get user ID
        from autogpt_libs.auth.jwt_utils import parse_jwt_token

        payload = parse_jwt_token(credentials.credentials)
        return payload.get("sub")
    except Exception as e:
        logger.debug(f"Auth token validation failed (anonymous access): {e}")
        return None
