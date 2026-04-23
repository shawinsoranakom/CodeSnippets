async def test_climate_get_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test states of the climate."""
    device = device_registry.async_get_device(identifiers={("freedompro", uid)})
    assert device is not None
    assert device.identifiers == {("freedompro", uid)}
    assert device.manufacturer == "Freedompro"
    assert device.name == "thermostat"
    assert device.model == "thermostat"

    entity_id = "climate.thermostat"
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes.get("friendly_name") == "thermostat"

    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
    ]

    assert state.attributes[ATTR_MIN_TEMP] == 7
    assert state.attributes[ATTR_MAX_TEMP] == 35
    assert state.attributes[ATTR_TEMPERATURE] == 14
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 14

    assert state.state == HVACMode.HEAT

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    states_response = get_states_response_for_uid(uid)
    states_response[0]["state"]["currentTemperature"] = 20
    states_response[0]["state"]["targetTemperature"] = 21
    with patch(
        "homeassistant.components.freedompro.coordinator.get_states",
        return_value=states_response,
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state
        assert state.attributes.get("friendly_name") == "thermostat"

        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.unique_id == uid

        assert state.attributes[ATTR_TEMPERATURE] == 21
        assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 20