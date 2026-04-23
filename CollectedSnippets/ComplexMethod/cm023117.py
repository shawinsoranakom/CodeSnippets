async def test_get_provisioning_entries(
    hass: HomeAssistant, integration, client, hass_ws_client: WebSocketGenerator
) -> None:
    """Test get_provisioning_entries websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {
        "entries": [{"dsk": "test", "securityClasses": [0], "fake": "test"}]
    }

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/get_provisioning_entries",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] == [
        {DSK: "test", SECURITY_CLASSES: [0], STATUS: 0, "fake": "test"}
    ]

    assert len(client.async_send_command.call_args_list) == 1
    assert client.async_send_command.call_args[0][0] == {
        "command": "controller.get_provisioning_entries",
    }

    # Test FailedZWaveCommand is caught
    with patch(
        f"{CONTROLLER_PATCH_PREFIX}.async_get_provisioning_entries",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 6,
                TYPE: "zwave_js/get_provisioning_entries",
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
        {ID: 7, TYPE: "zwave_js/get_provisioning_entries", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED