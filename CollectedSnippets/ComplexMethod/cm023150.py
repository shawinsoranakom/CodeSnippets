async def test_cancel_secure_bootstrap_s2(
    hass: HomeAssistant, client, integration, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that the cancel_secure_bootstrap_s2 WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    # Test successful cancellation
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/cancel_secure_bootstrap_s2",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "controller.cancel_secure_bootstrap_s2"

    # Test FailedZWaveCommand is caught
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_cancel_secure_bootstrap_s2",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/cancel_secure_bootstrap_s2",
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

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/cancel_secure_bootstrap_s2",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED

    # Test sending command with invalid entry ID fails
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/cancel_secure_bootstrap_s2",
            ENTRY_ID: "invalid_entry_id",
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND