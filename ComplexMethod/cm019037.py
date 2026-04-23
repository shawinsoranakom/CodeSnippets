async def test_websocket_update_preferences(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    cloud: MagicMock,
    setup_cloud: None,
) -> None:
    """Test updating preference."""
    assert cloud.client.prefs.google_enabled
    assert cloud.client.prefs.alexa_enabled
    assert cloud.client.prefs.google_secure_devices_pin is None
    assert cloud.client.prefs.remote_allow_remote_enable is True
    assert cloud.client.prefs.cloud_ice_servers_enabled is True

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "cloud/update_prefs",
            "alexa_enabled": False,
            "google_enabled": False,
            "google_secure_devices_pin": "1234",
            "tts_default_voice": ["en-GB", "RyanNeural"],
            "remote_allow_remote_enable": False,
            "cloud_ice_servers_enabled": False,
        }
    )
    response = await client.receive_json()

    assert response["success"]
    assert not cloud.client.prefs.google_enabled
    assert not cloud.client.prefs.alexa_enabled
    assert cloud.client.prefs.google_secure_devices_pin == "1234"
    assert cloud.client.prefs.remote_allow_remote_enable is False
    assert cloud.client.prefs.cloud_ice_servers_enabled is False
    assert cloud.client.prefs.tts_default_voice == ("en-GB", "RyanNeural")