async def test_thermostat_restore(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, hk_driver
) -> None:
    """Test setting up an entity from state in the event registry."""
    hass.set_state(CoreState.not_running)

    entity_registry.async_get_or_create(
        "climate", "generic", "1234", suggested_object_id="simple"
    )
    entity_registry.async_get_or_create(
        "climate",
        "generic",
        "9012",
        suggested_object_id="all_info_set",
        capabilities={
            ATTR_MIN_TEMP: 60,
            ATTR_MAX_TEMP: 70,
            ATTR_HVAC_MODES: [HVACMode.HEAT_COOL, HVACMode.OFF],
        },
        supported_features=0,
        original_device_class="mock-device-class",
    )

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START, {})
    await hass.async_block_till_done()

    entity_id = "climate.simple"
    hass.states.async_set(entity_id, HVACMode.OFF)

    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 2, None)
    assert acc.category == 9
    state = hass.states.get(entity_id)
    assert state
    assert acc.get_temperature_range(state) == (7, 35)
    assert set(acc.char_target_heat_cool.properties["ValidValues"].keys()) == {
        "cool",
        "heat",
        "heat_cool",
        "off",
    }

    entity_id = "climate.all_info_set"
    state = hass.states.get(entity_id)
    assert state

    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 3, None)
    assert acc.category == 9
    assert acc.get_temperature_range(state) == (60.0, 70.0)
    assert set(acc.char_target_heat_cool.properties["ValidValues"].keys()) == {
        "heat_cool",
        "off",
    }