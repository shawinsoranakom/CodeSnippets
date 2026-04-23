async def test_set_config_parameter(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client,
    multisensor_6,
    aeotec_zw164_siren,
    integration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the set_config_parameter service."""
    entity_entry = entity_registry.async_get(AIR_TEMPERATURE_SENSOR)

    # Test setting config parameter by property and property_key
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_PARAMETER_BITMASK: 1,
            ATTR_CONFIG_VALUE: 1,
        },
        blocking=True,
    )

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

    # Test setting config parameter value in hex
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_PARAMETER_BITMASK: 1,
            ATTR_CONFIG_VALUE: "0x1",
        },
        blocking=True,
    )

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

    # Test setting parameter by property name
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: "Group 2: Send battery reports",
            ATTR_CONFIG_VALUE: 1,
        },
        blocking=True,
    )

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

    # Test setting parameter by property name and state label
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_DEVICE_ID: entity_entry.device_id,
            ATTR_CONFIG_PARAMETER: "Temperature Threshold (Unit)",
            ATTR_CONFIG_VALUE: "Fahrenheit",
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 52
    assert args["valueId"] == {
        "commandClass": 112,
        "endpoint": 0,
        "property": 41,
        "propertyKey": 15,
    }
    assert args["value"] == 2

    client.async_send_command_no_wait.reset_mock()

    # Test using area ID
    area = area_registry.async_get_or_create("test")
    entity_registry.async_update_entity(entity_entry.entity_id, area_id=area.id)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_AREA_ID: area.id,
            ATTR_CONFIG_PARAMETER: "Temperature Threshold (Unit)",
            ATTR_CONFIG_VALUE: "Fahrenheit",
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 52
    assert args["valueId"] == {
        "commandClass": 112,
        "endpoint": 0,
        "property": 41,
        "propertyKey": 15,
    }
    assert args["value"] == 2

    client.async_send_command_no_wait.reset_mock()

    # Test setting parameter by property and bitmask
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_PARAMETER_BITMASK: "0x01",
            ATTR_CONFIG_VALUE: 1,
        },
        blocking=True,
    )

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

    # Test setting parameter by value_size
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 2,
            ATTR_VALUE_SIZE: 2,
            ATTR_VALUE_FORMAT: 1,
            ATTR_CONFIG_VALUE: 1,
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.set_raw_config_parameter_value"
    assert args["nodeId"] == 52
    assert args["endpoint"] == 0
    assert args["parameter"] == 2
    assert args["value"] == 1
    assert args["valueSize"] == 2
    assert args["valueFormat"] == 1

    client.async_send_command_no_wait.reset_mock()

    # Test setting parameter when one node has endpoint and other doesn't
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: [AIR_TEMPERATURE_SENSOR, "siren.indoor_siren_6_tone_id"],
            ATTR_ENDPOINT: 1,
            ATTR_CONFIG_PARAMETER: 32,
            ATTR_VALUE_SIZE: 2,
            ATTR_VALUE_FORMAT: 1,
            ATTR_CONFIG_VALUE: 1,
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 0
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "endpoint.set_raw_config_parameter_value"
    assert args["nodeId"] == 2
    assert args["endpoint"] == 1
    assert args["parameter"] == 32
    assert args["value"] == 1
    assert args["valueSize"] == 2
    assert args["valueFormat"] == 1

    client.async_send_command_no_wait.reset_mock()
    client.async_send_command.reset_mock()

    # Test groups get expanded
    assert await async_setup_component(hass, "group", {})
    await Group.async_create_group(
        hass,
        "test",
        created_by_service=False,
        entity_ids=[AIR_TEMPERATURE_SENSOR],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: "group.test",
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_PARAMETER_BITMASK: "0x01",
            ATTR_CONFIG_VALUE: 1,
        },
        blocking=True,
    )

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

    # Test that we can't include a bitmask value if parameter is a string
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CONFIG_PARAMETER,
            {
                ATTR_DEVICE_ID: entity_entry.device_id,
                ATTR_CONFIG_PARAMETER: "Temperature Threshold (Unit)",
                ATTR_CONFIG_PARAMETER_BITMASK: 1,
                ATTR_CONFIG_VALUE: "Fahrenheit",
            },
            blocking=True,
        )

    non_zwave_js_config_entry = MockConfigEntry(entry_id="fake_entry_id")
    non_zwave_js_config_entry.add_to_hass(hass)
    non_zwave_js_device = device_registry.async_get_or_create(
        config_entry_id=non_zwave_js_config_entry.entry_id,
        identifiers={("test", "test")},
    )

    zwave_js_device_with_invalid_node_id = device_registry.async_get_or_create(
        config_entry_id=integration.entry_id, identifiers={(DOMAIN, "500-500")}
    )

    non_zwave_js_entity = entity_registry.async_get_or_create(
        "test",
        "sensor",
        "test_sensor",
        suggested_object_id="test_sensor",
        config_entry=non_zwave_js_config_entry,
    )

    # Test unknown endpoint throws error when None are remaining
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CONFIG_PARAMETER,
            {
                ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
                ATTR_ENDPOINT: 5,
                ATTR_CONFIG_PARAMETER: 2,
                ATTR_VALUE_SIZE: 2,
                ATTR_VALUE_FORMAT: 1,
                ATTR_CONFIG_VALUE: 1,
            },
            blocking=True,
        )

    # Test that we can't include bitmask and value size and value format
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CONFIG_PARAMETER,
            {
                ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
                ATTR_CONFIG_PARAMETER: 102,
                ATTR_CONFIG_PARAMETER_BITMASK: 1,
                ATTR_CONFIG_VALUE: "Fahrenheit",
                ATTR_VALUE_FORMAT: 1,
                ATTR_VALUE_SIZE: 2,
            },
            blocking=True,
        )

    # Test that value size must be 1, 2, or 4 (not 3)
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CONFIG_PARAMETER,
            {
                ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
                ATTR_CONFIG_PARAMETER: 102,
                ATTR_CONFIG_PARAMETER_BITMASK: 1,
                ATTR_CONFIG_VALUE: "Fahrenheit",
                ATTR_VALUE_FORMAT: 1,
                ATTR_VALUE_SIZE: 3,
            },
            blocking=True,
        )

    # Test that a Z-Wave JS device with an invalid node ID, non Z-Wave JS entity,
    # non Z-Wave JS device, invalid device_id, and invalid node_id gets filtered out.
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: [
                AIR_TEMPERATURE_SENSOR,
                non_zwave_js_entity.entity_id,
                "sensor.fake",
            ],
            ATTR_DEVICE_ID: [
                zwave_js_device_with_invalid_node_id.id,
                non_zwave_js_device.id,
                "fake_device_id",
            ],
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_PARAMETER_BITMASK: "0x01",
            ATTR_CONFIG_VALUE: 1,
        },
        blocking=True,
    )

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

    # Test that when a device is awake, we call async_send_command instead of
    # async_send_command_no_wait
    multisensor_6.handle_wake_up(None)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_CONFIG_PARAMETER,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_PARAMETER_BITMASK: 1,
            ATTR_CONFIG_VALUE: 1,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 52
    assert args["valueId"] == {
        "commandClass": 112,
        "endpoint": 0,
        "property": 102,
        "propertyKey": 1,
    }
    assert args["value"] == 1

    client.async_send_command.reset_mock()

    # Test setting config parameter with no valid nodes raises Exception
    with pytest.raises(vol.MultipleInvalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CONFIG_PARAMETER,
            {
                ATTR_ENTITY_ID: "sensor.fake",
                ATTR_CONFIG_PARAMETER: 102,
                ATTR_CONFIG_PARAMETER_BITMASK: 1,
                ATTR_CONFIG_VALUE: 1,
            },
            blocking=True,
        )

    client.async_send_command_no_wait.reset_mock()
    client.async_send_command.reset_mock()

    caplog.clear()

    cmd_result = SetConfigParameterResult("accepted", {"status": 255})

    # Test accepted return
    with patch(
        "homeassistant.components.zwave_js.services.Endpoint.async_set_raw_config_parameter_value",
        return_value=cmd_result,
    ) as mock_set_raw_config_parameter_value:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CONFIG_PARAMETER,
            {
                ATTR_ENTITY_ID: ["siren.indoor_siren_6_tone_id"],
                ATTR_ENDPOINT: 0,
                ATTR_CONFIG_PARAMETER: 32,
                ATTR_VALUE_SIZE: 2,
                ATTR_VALUE_FORMAT: 1,
                ATTR_CONFIG_VALUE: 1,
            },
            blocking=True,
        )
        assert len(mock_set_raw_config_parameter_value.call_args_list) == 1
        assert mock_set_raw_config_parameter_value.call_args[0][0] == 1
        assert mock_set_raw_config_parameter_value.call_args[0][1] == 32
        assert mock_set_raw_config_parameter_value.call_args[1] == {
            "property_key": None,
            "value_size": 2,
            "value_format": 1,
        }

    assert "Set configuration parameter" in caplog.text
    caplog.clear()

    # Test queued return
    cmd_result.status = "queued"
    with patch(
        "homeassistant.components.zwave_js.services.Endpoint.async_set_raw_config_parameter_value",
        return_value=cmd_result,
    ) as mock_set_raw_config_parameter_value:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CONFIG_PARAMETER,
            {
                ATTR_ENTITY_ID: ["siren.indoor_siren_6_tone_id"],
                ATTR_ENDPOINT: 0,
                ATTR_CONFIG_PARAMETER: 32,
                ATTR_VALUE_SIZE: 2,
                ATTR_VALUE_FORMAT: 1,
                ATTR_CONFIG_VALUE: 1,
            },
            blocking=True,
        )
        assert len(mock_set_raw_config_parameter_value.call_args_list) == 1
        assert mock_set_raw_config_parameter_value.call_args[0][0] == 1
        assert mock_set_raw_config_parameter_value.call_args[0][1] == 32
        assert mock_set_raw_config_parameter_value.call_args[1] == {
            "property_key": None,
            "value_size": 2,
            "value_format": 1,
        }

    assert "Added command to queue" in caplog.text
    caplog.clear()