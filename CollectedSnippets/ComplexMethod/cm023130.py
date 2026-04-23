async def test_set_config_parameter(
    hass: HomeAssistant,
    multisensor_6,
    client,
    hass_ws_client: WebSocketGenerator,
    integration,
) -> None:
    """Test the set_config_parameter service."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    device = get_device(hass, multisensor_6)
    new_value_data = multisensor_6.values[
        get_value_id_str(multisensor_6, 112, 102, 0, 1)
    ].data.copy()
    new_value_data["endpoint"] = 1
    new_value = ConfigurationValue(multisensor_6, new_value_data)
    multisensor_6.values[get_value_id_str(multisensor_6, 112, 102, 1, 1)] = new_value

    client.async_send_command_no_wait.return_value = None

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/set_config_parameter",
            DEVICE_ID: device.id,
            PROPERTY: 102,
            PROPERTY_KEY: 1,
            VALUE: 1,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["status"] == "queued"

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 52
    assert args["valueId"] == {
        "commandClass": 112,
        "endpoint": 0,
        "property": 102,
        "propertyKey": 1,
    }
    assert args["value"] == 1

    client.async_send_command_no_wait.reset_mock()

    client.async_send_command_no_wait.return_value = None

    # Test using a different endpoint
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "zwave_js/set_config_parameter",
            DEVICE_ID: device.id,
            ENDPOINT: 1,
            PROPERTY: 102,
            PROPERTY_KEY: 1,
            VALUE: 1,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["status"] == "queued"

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 52
    assert args["valueId"] == {
        "commandClass": 112,
        "endpoint": 1,
        "property": 102,
        "propertyKey": 1,
    }
    assert args["value"] == 1

    client.async_send_command_no_wait.reset_mock()

    # Test that hex strings are accepted and converted as expected
    client.async_send_command_no_wait.return_value = None

    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/set_config_parameter",
            DEVICE_ID: device.id,
            PROPERTY: 102,
            PROPERTY_KEY: 1,
            VALUE: "0x1",
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["status"] == "queued"

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 52
    assert args["valueId"] == {
        "commandClass": 112,
        "endpoint": 0,
        "property": 102,
        "propertyKey": 1,
    }
    assert args["value"] == 1

    client.async_send_command_no_wait.reset_mock()

    with patch(
        "homeassistant.components.zwave_js.api.async_set_config_parameter",
    ) as set_param_mock:
        set_param_mock.side_effect = InvalidNewValue("test")
        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "zwave_js/set_config_parameter",
                DEVICE_ID: device.id,
                PROPERTY: 102,
                PROPERTY_KEY: 1,
                VALUE: 1,
            }
        )

        msg = await ws_client.receive_json()

        assert len(client.async_send_command_no_wait.call_args_list) == 0
        assert not msg["success"]
        assert msg["error"]["code"] == "not_supported"
        assert msg["error"]["message"] == "test"

        set_param_mock.side_effect = NotFoundError("test")
        await ws_client.send_json(
            {
                ID: 5,
                TYPE: "zwave_js/set_config_parameter",
                DEVICE_ID: device.id,
                PROPERTY: 102,
                PROPERTY_KEY: 1,
                VALUE: 1,
            }
        )

        msg = await ws_client.receive_json()

        assert len(client.async_send_command_no_wait.call_args_list) == 0
        assert not msg["success"]
        assert msg["error"]["code"] == "not_found"
        assert msg["error"]["message"] == "test"

        set_param_mock.side_effect = SetValueFailed("test")
        await ws_client.send_json(
            {
                ID: 6,
                TYPE: "zwave_js/set_config_parameter",
                DEVICE_ID: device.id,
                PROPERTY: 102,
                PROPERTY_KEY: 1,
                VALUE: 1,
            }
        )

        msg = await ws_client.receive_json()

        assert len(client.async_send_command_no_wait.call_args_list) == 0
        assert not msg["success"]
        assert msg["error"]["code"] == "unknown_error"
        assert msg["error"]["message"] == "test"

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 7,
            TYPE: "zwave_js/set_config_parameter",
            DEVICE_ID: "fake_device",
            PROPERTY: 102,
            PROPERTY_KEY: 1,
            VALUE: 1,
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test FailedZWaveCommand is caught
    with patch(
        "homeassistant.components.zwave_js.api.async_set_config_parameter",
        side_effect=FailedZWaveCommand("failed_command", 1, "error message"),
    ):
        await ws_client.send_json(
            {
                ID: 8,
                TYPE: "zwave_js/set_config_parameter",
                DEVICE_ID: device.id,
                PROPERTY: 102,
                PROPERTY_KEY: 1,
                VALUE: 1,
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
            ID: 9,
            TYPE: "zwave_js/set_config_parameter",
            DEVICE_ID: device.id,
            PROPERTY: 102,
            PROPERTY_KEY: 1,
            VALUE: 1,
        }
    )

    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED