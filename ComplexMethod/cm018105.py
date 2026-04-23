async def test_one_long_lived_access_token_per_refresh_token(mock_hass) -> None:
    """Test one refresh_token can only have one long-lived access token."""
    manager = await auth.auth_manager_from_config(mock_hass, [], [])
    user = MockUser().add_to_auth_manager(manager)
    refresh_token = await manager.async_create_refresh_token(
        user,
        client_name="GPS Logger",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=3000),
    )
    assert refresh_token.token_type == auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    access_token = manager.async_create_access_token(refresh_token)
    jwt_key = refresh_token.jwt_key

    rt = manager.async_validate_access_token(access_token)
    assert rt.id == refresh_token.id

    with pytest.raises(ValueError):
        await manager.async_create_refresh_token(
            user,
            client_name="GPS Logger",
            token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
            access_token_expiration=timedelta(days=3000),
        )

    manager.async_remove_refresh_token(refresh_token)
    assert refresh_token.id not in user.refresh_tokens
    rt = manager.async_validate_access_token(access_token)
    assert rt is None, "Previous issued access token has been invoked"

    refresh_token_2 = await manager.async_create_refresh_token(
        user,
        client_name="GPS Logger",
        token_type=auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
        access_token_expiration=timedelta(days=3000),
    )
    assert refresh_token_2.id != refresh_token.id
    assert refresh_token_2.token_type == auth_models.TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN
    access_token_2 = manager.async_create_access_token(refresh_token_2)
    jwt_key_2 = refresh_token_2.jwt_key

    assert access_token != access_token_2
    assert jwt_key != jwt_key_2

    rt = manager.async_validate_access_token(access_token_2)
    jwt_payload = jwt.decode(access_token_2, rt.jwt_key, algorithms=["HS256"])
    assert jwt_payload["iss"] == refresh_token_2.id
    assert (
        jwt_payload["exp"] - jwt_payload["iat"] == timedelta(days=3000).total_seconds()
    )