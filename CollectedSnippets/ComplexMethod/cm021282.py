async def test_themes_api(
    hass: HomeAssistant, themes_ws_client: MockHAClientWebSocket
) -> None:
    """Test that /api/themes returns correct data."""
    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "default"
    assert msg["result"]["default_dark_theme"] is None
    assert msg["result"]["themes"] == MOCK_THEMES

    # recovery mode
    hass.config.recovery_mode = True
    await themes_ws_client.send_json({"id": 6, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "default"
    assert msg["result"]["themes"] == {}

    # safe mode
    hass.config.recovery_mode = False
    hass.config.safe_mode = True
    await themes_ws_client.send_json({"id": 7, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    assert msg["result"]["default_theme"] == "default"
    assert msg["result"]["themes"] == {}