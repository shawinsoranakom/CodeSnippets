async def test_deactivate_user_removes_refresh_tokens(hass: HomeAssistant) -> None:
    """Test that deactivating a user removes their refresh tokens."""
    manager = await auth.auth_manager_from_config(hass, [], [])
    user = MockUser().add_to_auth_manager(manager)

    refresh_token1 = await manager.async_create_refresh_token(user, CLIENT_ID)
    refresh_token2 = await manager.async_create_refresh_token(user, "other-client")
    assert len(user.refresh_tokens) == 2
    assert manager.async_get_refresh_token(refresh_token1.id) == refresh_token1
    assert manager.async_get_refresh_token(refresh_token2.id) == refresh_token2

    await manager.async_deactivate_user(user)

    # Verify user is deactivated and all refresh tokens are removed
    assert user.is_active is False
    assert len(user.refresh_tokens) == 0
    assert manager.async_get_refresh_token(refresh_token1.id) is None
    assert manager.async_get_refresh_token(refresh_token2.id) is None