async def test_set_value(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    client,
    climate_danfoss_lc_13,
    integration,
) -> None:
    """Test set_value service."""
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, climate_danfoss_lc_13)}
    )
    assert device

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: CLIMATE_DANFOSS_LC13_ENTITY,
            ATTR_COMMAND_CLASS: 117,
            ATTR_PROPERTY: "local",
            ATTR_VALUE: 2,
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "commandClass": 117,
        "endpoint": 0,
        "property": "local",
    }
    assert args["value"] == 2

    client.async_send_command_no_wait.reset_mock()

    # Test bitmask as value and non bool as bool
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: CLIMATE_DANFOSS_LC13_ENTITY,
            ATTR_COMMAND_CLASS: 117,
            ATTR_PROPERTY: "local",
            ATTR_VALUE: "0x2",
            ATTR_WAIT_FOR_RESULT: 1,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "commandClass": 117,
        "endpoint": 0,
        "property": "local",
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test using area ID
    area = area_registry.async_get_or_create("test")
    device_registry.async_update_device(device.id, area_id=area.id)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_AREA_ID: area.id,
            ATTR_COMMAND_CLASS: 117,
            ATTR_PROPERTY: "local",
            ATTR_VALUE: "0x2",
            ATTR_WAIT_FOR_RESULT: 1,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "commandClass": 117,
        "endpoint": 0,
        "property": "local",
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test groups get expanded
    assert await async_setup_component(hass, "group", {})
    await Group.async_create_group(
        hass,
        "test",
        created_by_service=False,
        entity_ids=[CLIMATE_DANFOSS_LC13_ENTITY],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: "group.test",
            ATTR_COMMAND_CLASS: 117,
            ATTR_PROPERTY: "local",
            ATTR_VALUE: "0x2",
            ATTR_WAIT_FOR_RESULT: 1,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "commandClass": 117,
        "endpoint": 0,
        "property": "local",
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test that when a command fails we raise an exception
    client.async_send_command.return_value = {
        "result": {"status": 2, "message": "test"}
    }

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_DEVICE_ID: device.id,
                ATTR_COMMAND_CLASS: 117,
                ATTR_PROPERTY: "local",
                ATTR_VALUE: 2,
                ATTR_WAIT_FOR_RESULT: True,
            },
            blocking=True,
        )

    assert len(client.async_send_command.call_args_list) == 1

    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "commandClass": 117,
        "endpoint": 0,
        "property": "local",
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test missing device and entities keys
    with pytest.raises(vol.MultipleInvalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_COMMAND_CLASS: 117,
                ATTR_PROPERTY: "local",
                ATTR_VALUE: 2,
                ATTR_WAIT_FOR_RESULT: True,
            },
            blocking=True,
        )