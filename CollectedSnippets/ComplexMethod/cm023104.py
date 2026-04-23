async def test_preset_and_no_setpoint(
    hass: HomeAssistant, client, climate_eurotronic_spirit_z, integration
) -> None:
    """Test preset without setpoint value."""
    node = climate_eurotronic_spirit_z

    state = hass.states.get(CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY)
    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 22

    # Test setting preset mode Full power
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY,
            ATTR_PRESET_MODE: "Full power",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 8
    assert args["valueId"] == {
        "commandClass": 64,
        "endpoint": 0,
        "property": "mode",
    }
    assert args["value"] == 15

    client.async_send_command.reset_mock()

    # Test Full power preset update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 8,
            "args": {
                "commandClassName": "Thermostat Mode",
                "commandClass": 64,
                "endpoint": 0,
                "property": "mode",
                "propertyName": "mode",
                "newValue": 15,
                "prevValue": 1,
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY)
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] is None
    assert state.attributes[ATTR_PRESET_MODE] == "Full power"

    with pytest.raises(ServiceValidationError):
        # Test setting invalid preset mode
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                ATTR_ENTITY_ID: CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY,
                ATTR_PRESET_MODE: "invalid_preset",
            },
            blocking=True,
        )

    assert len(client.async_send_command.call_args_list) == 0

    client.async_send_command.reset_mock()

    # Restore hvac mode by setting preset None
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: CLIMATE_EUROTRONICS_SPIRIT_Z_ENTITY,
            ATTR_PRESET_MODE: PRESET_NONE,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 8
    assert args["valueId"]["commandClass"] == 64
    assert args["valueId"]["endpoint"] == 0
    assert args["valueId"]["property"] == "mode"
    assert args["value"] == 1

    client.async_send_command.reset_mock()