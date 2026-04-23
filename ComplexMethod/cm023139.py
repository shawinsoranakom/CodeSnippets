async def test_is_node_firmware_update_in_progress(
    hass: HomeAssistant,
    client,
    multisensor_6,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that the is_firmware_update_in_progress WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    device = get_device(hass, multisensor_6)

    client.async_send_command.return_value = {"progress": True}
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/is_node_firmware_update_in_progress",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.is_firmware_update_in_progress"
    assert args["nodeId"] == multisensor_6.node_id

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.node.Node.async_is_firmware_update_in_progress",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "zwave_js/is_node_firmware_update_in_progress",
                DEVICE_ID: device.id,
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
            TYPE: "zwave_js/is_node_firmware_update_in_progress",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED