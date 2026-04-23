async def test_create_user_once(hass: HomeAssistant) -> None:
    """Test that we reuse the user."""
    cur_users = len(await hass.auth.async_get_users())
    app = web.Application()
    await async_setup_auth(hass, app)
    users = await hass.auth.async_get_users()
    assert len(users) == cur_users + 1

    user: User = next((user for user in users if user.name == CONTENT_USER_NAME), None)
    assert user is not None, users

    assert len(user.groups) == 1
    assert user.groups[0].id == GROUP_ID_READ_ONLY
    assert len(user.refresh_tokens) == 1
    assert user.system_generated

    await async_setup_auth(hass, app)

    # test it did not create a user
    assert len(await hass.auth.async_get_users()) == cur_users + 1