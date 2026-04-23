async def test_set_preset_mode_manufacturer_specific(
    hass: HomeAssistant,
    client: MagicMock,
    climate_eurotronic_comet_z: Node,
    integration: MockConfigEntry,
) -> None:
    """Test setting preset mode to manufacturer specific.

    This tests the Eurotronic Comet Z thermostat which has a
    "Manufacturer specific" thermostat mode (value 31) that is
    exposed as a preset mode.
    """
    node = climate_eurotronic_comet_z
    entity_id = "climate.radiator_thermostat"

    state = hass.states.get(entity_id)
    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 21
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_NONE

    # Test setting preset mode to "Manufacturer specific"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_PRESET_MODE: "Manufacturer specific",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 64,
        "endpoint": 0,
        "property": "mode",
    }
    assert args["value"] == 31

    client.async_send_command.reset_mock()

    # Simulate the device updating to manufacturer specific mode
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 2,
            "args": {
                "commandClassName": "Thermostat Mode",
                "commandClass": 64,
                "endpoint": 0,
                "property": "mode",
                "propertyName": "mode",
                "newValue": 31,
                "prevValue": 1,
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity_id)
    assert state
    # Mode 31 is not in ZW_HVAC_MODE_MAP, so hvac_mode is unknown.
    assert state.state == "unknown"
    assert state.attributes[ATTR_PRESET_MODE] == "Manufacturer specific"

    # Test restoring hvac mode by setting preset to none.
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_PRESET_MODE: PRESET_NONE,
        },
        blocking=True,
    )

    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 2
    assert args["valueId"] == {
        "commandClass": 64,
        "endpoint": 0,
        "property": "mode",
    }
    assert args["value"] == 1

    client.async_send_command.reset_mock()