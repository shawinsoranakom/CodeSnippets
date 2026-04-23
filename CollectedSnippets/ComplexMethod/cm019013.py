async def test_remote_services(
    hass: HomeAssistant, hass_read_only_user: MockUser
) -> None:
    """Setup cloud component and test services."""
    cloud = hass.data[DATA_CLOUD]

    assert hass.services.has_service(DOMAIN, "remote_connect")
    assert hass.services.has_service(DOMAIN, "remote_disconnect")

    with patch("hass_nabucasa.remote.RemoteUI.connect") as mock_connect:
        await hass.services.async_call(DOMAIN, "remote_connect", blocking=True)
        await hass.async_block_till_done()

    assert mock_connect.called
    assert cloud.client.remote_autostart

    with patch("hass_nabucasa.remote.RemoteUI.disconnect") as mock_disconnect:
        await hass.services.async_call(DOMAIN, "remote_disconnect", blocking=True)
        await hass.async_block_till_done()

    assert mock_disconnect.called
    assert not cloud.client.remote_autostart

    # Test admin access required
    non_admin_context = Context(user_id=hass_read_only_user.id)

    with (
        patch("hass_nabucasa.remote.RemoteUI.connect") as mock_connect,
        pytest.raises(Unauthorized),
    ):
        await hass.services.async_call(
            DOMAIN, "remote_connect", blocking=True, context=non_admin_context
        )

    assert mock_connect.called is False

    with (
        patch("hass_nabucasa.remote.RemoteUI.disconnect") as mock_disconnect,
        pytest.raises(Unauthorized),
    ):
        await hass.services.async_call(
            DOMAIN, "remote_disconnect", blocking=True, context=non_admin_context
        )

    assert mock_disconnect.called is False