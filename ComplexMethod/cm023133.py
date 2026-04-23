async def test_get_raw_config_parameter(
    hass: HomeAssistant,
    multisensor_6,
    integration,
    client,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the get_raw_config_parameter websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    device = get_device(hass, multisensor_6)

    client.async_send_command.return_value = {"value": 1}

    # Test getting a raw config parameter value
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/get_raw_config_parameter",
            DEVICE_ID: device.id,
            PROPERTY: 102,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["value"] == 1

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "endpoint.get_raw_config_parameter_value"
    assert args["nodeId"] == multisensor_6.node_id
    assert args["parameter"] == 102

    client.async_send_command.reset_mock()

    # Test FailedZWaveCommand is caught
    with patch(
        "zwave_js_server.model.node.Node.async_get_raw_config_parameter_value",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json_auto_id(
            {
                TYPE: "zwave_js/get_raw_config_parameter",
                DEVICE_ID: device.id,
                PROPERTY: 102,
            }
        )
        msg = await ws_client.receive_json()

        assert not msg["success"]
        assert msg["error"]["code"] == "zwave_error"
        assert msg["error"]["message"] == "zwave_error: Z-Wave error 1 - error message"

    # Test getting non-existent node fails
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/get_raw_config_parameter",
            DEVICE_ID: "fake_device",
            PROPERTY: 102,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test FailedCommand exception
    client.async_send_command.side_effect = FailedCommand("test", "test")
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/get_raw_config_parameter",
            DEVICE_ID: device.id,
            PROPERTY: 102,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "test"
    assert msg["error"]["message"] == "Command failed: test"

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/get_raw_config_parameter",
            DEVICE_ID: device.id,
            PROPERTY: 102,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED