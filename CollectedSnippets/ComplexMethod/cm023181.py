async def test_bulk_set_config_parameters(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    client,
    multisensor_6,
    integration,
) -> None:
    """Test the bulk_set_partial_config_parameters service."""
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, multisensor_6)}
    )
    assert device

    # Test setting config parameter by property and property_key
    await hass.services.async_call(
        DOMAIN,
        SERVICE_BULK_SET_PARTIAL_CONFIG_PARAMETERS,
        {
            ATTR_DEVICE_ID: device.id,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_VALUE: 241,
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
    }
    assert args["value"] == 241

    client.async_send_command_no_wait.reset_mock()

    # Test using area ID
    area = area_registry.async_get_or_create("test")
    device_registry.async_update_device(device.id, area_id=area.id)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_BULK_SET_PARTIAL_CONFIG_PARAMETERS,
        {
            ATTR_AREA_ID: area.id,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_VALUE: 241,
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
    }
    assert args["value"] == 241

    client.async_send_command_no_wait.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_BULK_SET_PARTIAL_CONFIG_PARAMETERS,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_VALUE: {
                1: 1,
                16: 1,
                32: 1,
                64: 1,
                128: 1,
            },
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
    }
    assert args["value"] == 241

    client.async_send_command_no_wait.reset_mock()

    # Test using hex values for config parameter values
    await hass.services.async_call(
        DOMAIN,
        SERVICE_BULK_SET_PARTIAL_CONFIG_PARAMETERS,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_VALUE: {
                1: "0x1",
                16: "0x1",
                32: "0x1",
                64: "0x1",
                128: "0x1",
            },
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
    }
    assert args["value"] == 241

    client.async_send_command_no_wait.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_BULK_SET_PARTIAL_CONFIG_PARAMETERS,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_VALUE: {
                "0x1": 1,
                "0x10": 1,
                "0x20": 1,
                "0x40": 1,
                "0x80": 1,
            },
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
    }
    assert args["value"] == 241

    client.async_send_command_no_wait.reset_mock()

    # Test that when a device is awake, we call async_send_command instead of
    # async_send_command_no_wait
    multisensor_6.handle_wake_up(None)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_BULK_SET_PARTIAL_CONFIG_PARAMETERS,
        {
            ATTR_ENTITY_ID: AIR_TEMPERATURE_SENSOR,
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_VALUE: {
                1: 1,
                16: 1,
                32: 1,
                64: 1,
                128: 1,
            },
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
    }
    assert args["value"] == 241

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
        SERVICE_BULK_SET_PARTIAL_CONFIG_PARAMETERS,
        {
            ATTR_ENTITY_ID: "group.test",
            ATTR_CONFIG_PARAMETER: 102,
            ATTR_CONFIG_VALUE: {
                1: 1,
                16: 1,
                32: 1,
                64: 1,
                128: 1,
            },
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
    }
    assert args["value"] == 241

    client.async_send_command.reset_mock()