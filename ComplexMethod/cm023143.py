async def test_install_config_update(
    hass: HomeAssistant, client, integration, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that the install_config_update WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    # Test we can get log configuration
    client.async_send_command.return_value = {"success": True}
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/install_config_update",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["result"]
    assert msg["success"]

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.driver.Driver.async_install_config_update",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "zwave_js/install_config_update",
                ENTRY_ID: entry.entry_id,
            }
        )
        msg = await ws_client.receive_json()

        assert not msg["success"]
        assert msg["error"]["code"] == "zwave_error"
        assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/install_config_update",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/install_config_update",
            ENTRY_ID: "INVALID",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND