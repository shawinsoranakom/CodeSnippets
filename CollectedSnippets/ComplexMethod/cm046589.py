async def _get_current_subject(
    credentials: HTTPAuthorizationCredentials,
    *,
    allow_password_change: bool,
) -> str:
    """
    FastAPI dependency to validate the JWT and return the subject.

    Use this as a dependency on routes that should be protected, e.g.:

        @router.get("/secure")
        async def secure_endpoint(current_subject: str = Depends(get_current_subject)):
            ...
    """
    token = credentials.credentials

    # --- API key path (sk-unsloth-...) ---
    if token.startswith(API_KEY_PREFIX):
        username = validate_api_key(token)
        if username is None:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Invalid or expired API key",
            )
        return username

    # --- JWT path ---
    subject = _decode_subject_without_verification(token)
    if subject is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid token payload",
        )

    record = get_user_and_secret(subject)
    if record is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired token",
        )

    _salt, _pwd_hash, jwt_secret, must_change_password = record
    try:
        payload = jwt.decode(token, jwt_secret, algorithms = [ALGORITHM])
        if payload.get("sub") != subject:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Invalid token payload",
            )
        if must_change_password and not allow_password_change:
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN,
                detail = "Password change required",
            )
        return subject
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired token",
        )