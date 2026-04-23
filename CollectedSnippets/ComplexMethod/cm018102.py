async def test_generating_system_user(hass: HomeAssistant) -> None:
    """Test that we can add a system user."""
    events = []

    @callback
    def user_added(event):
        events.append(event)

    hass.bus.async_listen("user_added", user_added)

    manager = await auth.auth_manager_from_config(hass, [], [])
    user = await manager.async_create_system_user("Hass.io")
    token = await manager.async_create_refresh_token(user)
    assert user.system_generated
    assert user.groups == []
    assert not user.local_only
    assert token is not None
    assert token.client_id is None
    assert token.token_type == auth.models.TOKEN_TYPE_SYSTEM
    assert token.expire_at is None

    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["user_id"] == user.id

    # Passing arguments
    user = await manager.async_create_system_user(
        "Hass.io", group_ids=[GROUP_ID_ADMIN], local_only=True
    )
    token = await manager.async_create_refresh_token(user)
    assert user.system_generated
    assert user.is_admin
    assert user.local_only
    assert token is not None
    assert token.client_id is None
    assert token.token_type == auth.models.TOKEN_TYPE_SYSTEM
    assert token.expire_at is None

    await hass.async_block_till_done()
    assert len(events) == 2
    assert events[1].data["user_id"] == user.id