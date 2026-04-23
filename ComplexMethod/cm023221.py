async def test_get_action_capabilities(
    hass: HomeAssistant,
    client: Client,
    climate_radio_thermostat_ct100_plus: Node,
    integration: ConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test we get the expected action capabilities."""
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, climate_radio_thermostat_ct100_plus)}
    )
    assert device

    # Test refresh_value
    capabilities = await device_action.async_get_action_capabilities(
        hass,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device.id,
            "type": "refresh_value",
        },
    )
    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "type": "boolean",
            "name": "refresh_all_values",
            "optional": True,
            "required": False,
        }
    ]

    # Test ping
    capabilities = await device_action.async_get_action_capabilities(
        hass,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device.id,
            "type": "ping",
        },
    )
    assert not capabilities

    # Test set_value
    capabilities = await device_action.async_get_action_capabilities(
        hass,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device.id,
            "type": "set_value",
        },
    )
    assert capabilities and "extra_fields" in capabilities

    cc_options = [
        ("133", "Association"),
        ("89", "Association Group Information"),
        ("128", "Battery"),
        ("129", "Clock"),
        ("112", "Configuration"),
        ("90", "Device Reset Locally"),
        ("122", "Firmware Update Meta Data"),
        ("135", "Indicator"),
        ("114", "Manufacturer Specific"),
        ("96", "Multi Channel"),
        ("142", "Multi Channel Association"),
        ("49", "Multilevel Sensor"),
        ("115", "Powerlevel"),
        ("68", "Thermostat Fan Mode"),
        ("69", "Thermostat Fan State"),
        ("64", "Thermostat Mode"),
        ("66", "Thermostat Operating State"),
        ("67", "Thermostat Setpoint"),
        ("134", "Version"),
        ("94", "Z-Wave Plus Info"),
    ]

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "command_class",
            "required": True,
            "options": cc_options,
            "type": "select",
        },
        {"name": "property", "required": True, "type": "string"},
        {"name": "property_key", "optional": True, "required": False, "type": "string"},
        {"name": "endpoint", "optional": True, "required": False, "type": "string"},
        {"name": "value", "required": True, "type": "string"},
        {
            "type": "boolean",
            "name": "wait_for_result",
            "optional": True,
            "required": False,
        },
    ]

    # Test enumerated type param
    capabilities = await device_action.async_get_action_capabilities(
        hass,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device.id,
            "type": "set_config_parameter",
            "endpoint": 0,
            "parameter": 1,
            "bitmask": None,
            "subtype": "1 (Temperature Reporting Threshold)",
        },
    )
    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "value",
            "required": True,
            "options": [
                ("0", "Disabled"),
                ("1", "0.5° F"),
                ("2", "1.0° F"),
                ("3", "1.5° F"),
                ("4", "2.0° F"),
            ],
            "type": "select",
        }
    ]

    # Test range type param
    capabilities = await device_action.async_get_action_capabilities(
        hass,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device.id,
            "type": "set_config_parameter",
            "endpoint": 0,
            "parameter": 10,
            "bitmask": None,
            "subtype": "10 (Temperature Reporting Filter)",
        },
    )
    assert capabilities and "extra_fields" in capabilities

    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "value",
            "required": True,
            "type": "integer",
            "valueMin": 0,
            "valueMax": 124,
        }
    ]

    # Test undefined type param
    capabilities = await device_action.async_get_action_capabilities(
        hass,
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device.id,
            "type": "set_config_parameter",
            "endpoint": 0,
            "parameter": 2,
            "bitmask": None,
            "subtype": "2 (HVAC Settings)",
        },
    )
    assert not capabilities