async def test_set_preset_mode_mapped_preset(
    hass: HomeAssistant,
    client: MagicMock,
    climate_eurotronic_comet_z: Node,
    integration: MockConfigEntry,
) -> None:
    """Test that a preset mapping to a supported HVAC mode shows that mode.

    The Eurotronic Comet Z has "Energy heat" (mode 11 = HEATING_ECON) which
    maps to HVACMode.HEAT in ZW_HVAC_MODE_MAP. Since the device supports
    heat, hvac_mode should return heat while in this preset.
    """
    node = climate_eurotronic_comet_z
    entity_id = "climate.radiator_thermostat"

    state = hass.states.get(entity_id)
    assert state
    assert state.state == HVACMode.HEAT

    # Set preset mode to "Energy heat"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_PRESET_MODE: "Energy heat",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["value"] == 11

    client.async_send_command.reset_mock()

    # Simulate the device updating to energy heat mode
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
                "newValue": 11,
                "prevValue": 1,
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity_id)
    assert state
    # Energy heat (HEATING_ECON) maps to HVACMode.HEAT which the device
    # supports, so hvac_mode returns heat.
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_PRESET_MODE] == "Energy heat"

    # Clear preset - should restore to heat (the mapped mode).
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
    assert args["value"] == 1

    client.async_send_command.reset_mock()