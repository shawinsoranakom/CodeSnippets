async def test_set_preset_mode_none_unmapped_preset(
    hass: HomeAssistant,
    client: MagicMock,
    climate_eurotronic_comet_z: Node,
    integration: MockConfigEntry,
) -> None:
    """Test clearing an unmapped preset falls back to first supported HVAC mode.

    When the device is in a preset mode that has no mapping in ZW_HVAC_MODE_MAP
    (e.g. "Manufacturer specific"), hvac_mode returns None. Setting preset to
    none should fall back to the first supported non-off HVAC mode.
    """
    node = climate_eurotronic_comet_z
    entity_id = "climate.radiator_thermostat"

    # Simulate the device being externally changed to "Manufacturer specific"
    # mode without HA having set a preset first.
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
    assert state.state == "unknown"
    assert state.attributes[ATTR_PRESET_MODE] == "Manufacturer specific"

    client.async_send_command.reset_mock()

    # Setting preset to none should default to heat since there is no
    # stored previous HVAC mode.
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