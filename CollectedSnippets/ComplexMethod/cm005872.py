async def test_create_user_tokens(auth_service: AuthService):
    """Test creating access and refresh tokens."""
    user_id = uuid4()
    db = AsyncMock()

    result = await auth_service.create_user_tokens(user_id, db, update_last_login=False)

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"  # noqa: S105 - not a password

    # Verify access token claims
    access_claims = jwt.decode(result["access_token"], options={"verify_signature": False})
    assert access_claims["sub"] == str(user_id)
    assert access_claims["type"] == "access"

    # Verify refresh token claims
    refresh_claims = jwt.decode(result["refresh_token"], options={"verify_signature": False})
    assert refresh_claims["sub"] == str(user_id)
    assert refresh_claims["type"] == "refresh"