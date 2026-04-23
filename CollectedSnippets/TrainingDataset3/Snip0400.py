def parse_jwt_token(token: str) -> dict[str, Any]:
    """
    Parse and validate a JWT token.

    :param token: The token to parse
    :return: The decoded payload
    :raises ValueError: If the token is invalid or expired
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_VERIFY_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
