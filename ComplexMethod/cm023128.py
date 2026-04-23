async def test_refresh_node_values(
    hass: HomeAssistant,
    client,
    multisensor_6,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that the refresh_node_values WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    device = get_device(hass, multisensor_6)

    client.async_send_command_no_wait.return_value = None
    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/refresh_node_values",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.refresh_values"
    assert args["nodeId"] == 52

    client.async_send_command_no_wait.reset_mock()

    # Test getting non-existent device fails
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/refresh_node_values",
            DEVICE_ID: "fake_device",
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.node.Node.async_refresh_values",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "zwave_js/refresh_node_values",
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
            ID: 5,
            TYPE: "zwave_js/refresh_node_values",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED