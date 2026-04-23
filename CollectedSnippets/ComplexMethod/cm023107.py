async def test_set_preset_mode_none_while_in_hvac_mode(
    hass: HomeAssistant,
    client: MagicMock,
    climate_eurotronic_comet_z: Node,
    integration: MockConfigEntry,
) -> None:
    """Test setting preset mode to none while already in an HVAC mode."""
    entity_id = "climate.radiator_thermostat"

    state = hass.states.get(entity_id)
    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_NONE

    # Setting preset to none while already in an HVAC mode restores
    # the current hvac mode.
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