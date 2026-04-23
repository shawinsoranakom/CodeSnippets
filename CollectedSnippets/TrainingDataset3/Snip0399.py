async def get_jwt_payload(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_jwt_auth),
) -> dict[str, Any]:
    """
    Extract and validate JWT payload from HTTP Authorization header.

    This is the core authentication function that handles:
    - Reading the `Authorization` header to obtain the JWT token
    - Verifying the JWT token's signature
    - Decoding the JWT token's payload

    :param credentials: HTTP Authorization credentials from bearer token
    :return: JWT payload dictionary
    :raises HTTPException: 401 if authentication fails
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    try:
        payload = parse_jwt_token(credentials.credentials)
        logger.debug("Token decoded successfully")
        return payload
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
