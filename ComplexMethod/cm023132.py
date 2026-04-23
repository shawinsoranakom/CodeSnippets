async def test_set_raw_config_parameter(
    hass: HomeAssistant,
    client,
    multisensor_6,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that the set_raw_config_parameter WS API call works."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    device = get_device(hass, multisensor_6)

    # Change from async_send_command to async_send_command_no_wait
    client.async_send_command_no_wait.return_value = None

    # Test setting a raw config parameter value
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/set_raw_config_parameter",
            DEVICE_ID: device.id,
            PROPERTY: 102,
            VALUE: 1,
            VALUE_SIZE: 2,
            VALUE_FORMAT: 1,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["status"] == "queued"

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.set_raw_config_parameter_value"
    assert args["nodeId"] == multisensor_6.node_id
    assert args["parameter"] == 102
    assert args["value"] == 1
    assert args["valueSize"] == 2
    assert args["valueFormat"] == 1

    # Reset the mock for async_send_command_no_wait instead
    client.async_send_command_no_wait.reset_mock()

    # Test getting non-existent node fails
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/set_raw_config_parameter",
            DEVICE_ID: "fake_device",
            PROPERTY: 102,
            VALUE: 1,
            VALUE_SIZE: 2,
            VALUE_FORMAT: 1,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/set_raw_config_parameter",
            DEVICE_ID: device.id,
            PROPERTY: 102,
            VALUE: 1,
            VALUE_SIZE: 2,
            VALUE_FORMAT: 1,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED