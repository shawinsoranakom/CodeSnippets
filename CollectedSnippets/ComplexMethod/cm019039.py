async def test_enabling_remote_remote_activation_not_allowed(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    cloud: MagicMock,
    setup_cloud: None,
) -> None:
    """Test we can enable remote UI locally when blocked remotely."""
    client = await hass_ws_client(hass)
    mock_connect = cloud.remote.connect
    assert not cloud.client.remote_autostart
    await cloud.client.prefs.async_update(remote_allow_remote_enable=False)

    await client.send_json({"id": 5, "type": "cloud/remote/connect"})
    response = await client.receive_json()

    assert response["success"]
    assert cloud.client.remote_autostart
    assert mock_connect.call_count == 1

    mock_disconnect = cloud.remote.disconnect

    await client.send_json({"id": 6, "type": "cloud/remote/disconnect"})
    response = await client.receive_json()

    assert response["success"]
    assert not cloud.client.remote_autostart
    assert mock_disconnect.call_count == 1