async def test_multicast_set_value(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    client,
    climate_danfoss_lc_13,
    climate_eurotronic_spirit_z,
    integration,
) -> None:
    """Test multicast_set_value service."""
    # Test successful multicast call
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MULTICAST_SET_VALUE,
        {
            ATTR_ENTITY_ID: [
                CLIMATE_DANFOSS_LC13_ENTITY,
                CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY,
            ],
            ATTR_COMMAND_CLASS: 67,
            ATTR_PROPERTY: "setpoint",
            ATTR_PROPERTY_KEY: 1,
            ATTR_VALUE: 2,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "multicast_group.set_value"
    assert args["nodeIDs"] == [
        climate_eurotronic_spirit_z.node_id,
        climate_danfoss_lc_13.node_id,
    ]
    assert args["valueId"] == {
        "commandClass": 67,
        "property": "setpoint",
        "propertyKey": 1,
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test successful multicast call with hex value
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MULTICAST_SET_VALUE,
        {
            ATTR_ENTITY_ID: [
                CLIMATE_DANFOSS_LC13_ENTITY,
                CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY,
            ],
            ATTR_COMMAND_CLASS: 67,
            ATTR_PROPERTY: "setpoint",
            ATTR_PROPERTY_KEY: 1,
            ATTR_VALUE: "0x2",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "multicast_group.set_value"
    assert args["nodeIDs"] == [
        climate_eurotronic_spirit_z.node_id,
        climate_danfoss_lc_13.node_id,
    ]
    assert args["valueId"] == {
        "commandClass": 67,
        "property": "setpoint",
        "propertyKey": 1,
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test using area ID
    device_eurotronic = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, climate_eurotronic_spirit_z)}
    )
    assert device_eurotronic
    device_danfoss = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, climate_danfoss_lc_13)}
    )
    assert device_danfoss
    area = area_registry.async_get_or_create("test")
    device_registry.async_update_device(device_eurotronic.id, area_id=area.id)
    device_registry.async_update_device(device_danfoss.id, area_id=area.id)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MULTICAST_SET_VALUE,
        {
            ATTR_AREA_ID: area.id,
            ATTR_COMMAND_CLASS: 67,
            ATTR_PROPERTY: "setpoint",
            ATTR_PROPERTY_KEY: 1,
            ATTR_VALUE: "0x2",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "multicast_group.set_value"
    assert args["nodeIDs"] == [
        climate_eurotronic_spirit_z.node_id,
        climate_danfoss_lc_13.node_id,
    ]
    assert args["valueId"] == {
        "commandClass": 67,
        "property": "setpoint",
        "propertyKey": 1,
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test groups get expanded for multicast call
    assert await async_setup_component(hass, "group", {})
    await Group.async_create_group(
        hass,
        "test",
        created_by_service=False,
        entity_ids=[CLIMATE_DANFOSS_LC13_ENTITY, CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MULTICAST_SET_VALUE,
        {
            ATTR_ENTITY_ID: "group.test",
            ATTR_COMMAND_CLASS: 67,
            ATTR_PROPERTY: "setpoint",
            ATTR_PROPERTY_KEY: 1,
            ATTR_VALUE: "0x2",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "multicast_group.set_value"
    assert args["nodeIDs"] == [
        climate_eurotronic_spirit_z.node_id,
        climate_danfoss_lc_13.node_id,
    ]
    assert args["valueId"] == {
        "commandClass": 67,
        "property": "setpoint",
        "propertyKey": 1,
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test successful broadcast call
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MULTICAST_SET_VALUE,
        {
            ATTR_BROADCAST: True,
            ATTR_COMMAND_CLASS: 67,
            ATTR_PROPERTY: "setpoint",
            ATTR_PROPERTY_KEY: 1,
            ATTR_VALUE: 2,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "broadcast_node.set_value"
    assert args["valueId"] == {
        "commandClass": 67,
        "property": "setpoint",
        "propertyKey": 1,
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test sending one node without broadcast uses the node.set_value command instead
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MULTICAST_SET_VALUE,
        {
            ATTR_ENTITY_ID: CLIMATE_DANFOSS_LC13_ENTITY,
            ATTR_COMMAND_CLASS: 67,
            ATTR_PROPERTY: "setpoint",
            ATTR_PROPERTY_KEY: 1,
            ATTR_VALUE: 2,
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.set_value"

    client.async_send_command_no_wait.reset_mock()

    # Test no device, entity, or broadcast flag raises error
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MULTICAST_SET_VALUE,
            {
                ATTR_COMMAND_CLASS: 67,
                ATTR_PROPERTY: "setpoint",
                ATTR_PROPERTY_KEY: 1,
                ATTR_VALUE: 2,
            },
            blocking=True,
        )

    # Test that when a command is unsuccessful we raise an exception
    client.async_send_command.return_value = {
        "result": {"status": 2, "message": "test"}
    }

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MULTICAST_SET_VALUE,
            {
                ATTR_ENTITY_ID: [
                    CLIMATE_DANFOSS_LC13_ENTITY,
                    CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY,
                ],
                ATTR_COMMAND_CLASS: 67,
                ATTR_PROPERTY: "setpoint",
                ATTR_PROPERTY_KEY: 1,
                ATTR_VALUE: 2,
            },
            blocking=True,
        )

    client.async_send_command.reset_mock()

    # Test that when we get an exception from the library we raise an exception
    client.async_send_command.side_effect = FailedZWaveCommand("test", 12, "test")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MULTICAST_SET_VALUE,
            {
                ATTR_ENTITY_ID: [
                    CLIMATE_DANFOSS_LC13_ENTITY,
                    CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY,
                ],
                ATTR_COMMAND_CLASS: 67,
                ATTR_PROPERTY: "setpoint",
                ATTR_PROPERTY_KEY: 1,
                ATTR_VALUE: 2,
            },
            blocking=True,
        )

    client.async_send_command.reset_mock()

    # Create a fake node with a different home ID from a real node and patch it into
    # return of helper function to check the validation for two nodes having different
    # home IDs
    diff_network_node = MagicMock()
    diff_network_node.client.driver.controller.home_id.return_value = "diff_home_id"

    with (
        pytest.raises(vol.MultipleInvalid),
        patch(
            "homeassistant.components.zwave_js.helpers.async_get_node_from_device_id",
            side_effect=(climate_danfoss_lc_13, diff_network_node),
        ),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MULTICAST_SET_VALUE,
            {
                ATTR_ENTITY_ID: [
                    CLIMATE_DANFOSS_LC13_ENTITY,
                ],
                ATTR_DEVICE_ID: "fake_device_id",
                ATTR_COMMAND_CLASS: 67,
                ATTR_PROPERTY: "setpoint",
                ATTR_PROPERTY_KEY: 1,
                ATTR_VALUE: 2,
            },
            blocking=True,
        )

    # Test that when there are multiple zwave_js config entries, service will fail
    # without devices or entities
    new_entry = MockConfigEntry(domain=DOMAIN)
    new_entry.add_to_hass(hass)
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_MULTICAST_SET_VALUE,
            {
                ATTR_BROADCAST: True,
                ATTR_COMMAND_CLASS: 67,
                ATTR_PROPERTY: "setpoint",
                ATTR_PROPERTY_KEY: 1,
                ATTR_VALUE: 2,
            },
            blocking=True,
        )