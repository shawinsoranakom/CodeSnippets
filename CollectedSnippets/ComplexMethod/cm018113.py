async def test_add_remove_user_affects_tokens(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test adding and removing a user removes the tokens."""
    store = auth_store.AuthStore(hass)
    await store.async_load()
    user = await store.async_create_user("Test User")
    assert user.name == "Test User"
    refresh_token = await store.async_create_refresh_token(
        user, "client_id", "access_token_expiration"
    )
    assert user.refresh_tokens == {refresh_token.id: refresh_token}
    assert await store.async_get_user(user.id) == user
    assert store.async_get_refresh_token(refresh_token.id) == refresh_token
    assert store.async_get_refresh_token_by_token(refresh_token.token) == refresh_token
    await store.async_remove_user(user)
    assert store.async_get_refresh_token(refresh_token.id) is None
    assert store.async_get_refresh_token_by_token(refresh_token.token) is None
    assert user.refresh_tokens == {}