async def test_async_user_not_allowed_do_auth(
    hass: HomeAssistant, app: web.Application
) -> None:
    """Test for not allowing auth."""
    user = await hass.auth.async_create_user("Hello")
    user.is_active = False

    # User not active
    assert async_user_not_allowed_do_auth(hass, user) == "User is not active"

    user.is_active = True
    user.local_only = True

    # No current request
    assert (
        async_user_not_allowed_do_auth(hass, user)
        == "No request available to validate local access"
    )

    trusted_request = Mock(remote="192.168.1.123")
    untrusted_request = Mock(remote=UNTRUSTED_ADDRESSES[0])

    # Is Remote IP and local only (cloud not loaded)
    assert async_user_not_allowed_do_auth(hass, user, trusted_request) is None
    assert (
        async_user_not_allowed_do_auth(hass, user, untrusted_request)
        == "User cannot authenticate remotely"
    )

    # Mimic cloud loaded and validate local IP again
    hass.config.components.add("cloud")
    assert async_user_not_allowed_do_auth(hass, user, trusted_request) is None
    assert (
        async_user_not_allowed_do_auth(hass, user, untrusted_request)
        == "User cannot authenticate remotely"
    )

    # Is Cloud request and local only, even a local IP will fail
    with patch(
        "hass_nabucasa.remote.is_cloud_request", Mock(get=Mock(return_value=True))
    ):
        assert (
            async_user_not_allowed_do_auth(hass, user, trusted_request)
            == "User is local only"
        )