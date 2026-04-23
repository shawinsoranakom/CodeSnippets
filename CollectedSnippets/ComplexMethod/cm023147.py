async def test_invoke_cc_api(
    hass: HomeAssistant,
    client,
    climate_radio_thermostat_ct100_plus_different_endpoints: Node,
    integration: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the invoke_cc_api websocket command."""
    ws_client = await hass_ws_client(hass)

    device_radio_thermostat = get_device(
        hass, climate_radio_thermostat_ct100_plus_different_endpoints
    )
    assert device_radio_thermostat

    # Test successful invoke_cc_api call with a static endpoint
    client.async_send_command.return_value = {"response": True}
    client.async_send_command_no_wait.return_value = {"response": True}

    # Test with wait_for_result=False (default)
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/invoke_cc_api",
            DEVICE_ID: device_radio_thermostat.id,
            ATTR_COMMAND_CLASS: 67,
            ATTR_METHOD_NAME: "someMethod",
            ATTR_PARAMETERS: [1, 2],
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] is None  # We did not specify wait_for_result=True

    await hass.async_block_till_done()

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args == {
        "command": "endpoint.invoke_cc_api",
        "nodeId": 26,
        "endpoint": 0,
        "commandClass": 67,
        "methodName": "someMethod",
        "args": [1, 2],
    }

    client.async_send_command_no_wait.reset_mock()

    # Test with wait_for_result=True
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/invoke_cc_api",
            DEVICE_ID: device_radio_thermostat.id,
            ATTR_COMMAND_CLASS: 67,
            ATTR_ENDPOINT: 0,
            ATTR_METHOD_NAME: "someMethod",
            ATTR_PARAMETERS: [1, 2],
            ATTR_WAIT_FOR_RESULT: True,
        }
    )
    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] is True

    await hass.async_block_till_done()

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args == {
        "command": "endpoint.invoke_cc_api",
        "nodeId": 26,
        "endpoint": 0,
        "commandClass": 67,
        "methodName": "someMethod",
        "args": [1, 2],
    }

    client.async_send_command.side_effect = NotFoundError

    # Ensure an error is returned
    await ws_client.send_json_auto_id(
        {
            TYPE: "zwave_js/invoke_cc_api",
            DEVICE_ID: device_radio_thermostat.id,
            ATTR_COMMAND_CLASS: 67,
            ATTR_ENDPOINT: 0,
            ATTR_METHOD_NAME: "someMethod",
            ATTR_PARAMETERS: [1, 2],
            ATTR_WAIT_FOR_RESULT: True,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {"code": "NotFoundError", "message": ""}