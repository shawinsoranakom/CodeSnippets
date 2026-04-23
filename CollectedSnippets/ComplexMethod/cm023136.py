async def test_get_log_config(
    hass: HomeAssistant, client, integration, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that the get_log_config WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    # Test we can get log configuration
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/get_log_config",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["result"]
    assert msg["success"]

    log_config = msg["result"]
    assert log_config["enabled"]
    assert log_config["level"] == LogLevel.INFO
    assert log_config["log_to_file"] is False
    assert log_config["filename"] == ""
    assert log_config["force_console"] is False

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/get_log_config",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED