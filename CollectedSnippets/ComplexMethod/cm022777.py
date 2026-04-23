async def test_water_heater_restore(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, hk_driver
) -> None:
    """Test setting up an entity from state in the event registry."""
    hass.set_state(CoreState.not_running)

    entity_registry.async_get_or_create(
        "water_heater", "generic", "1234", suggested_object_id="simple"
    )
    entity_registry.async_get_or_create(
        "water_heater",
        "generic",
        "9012",
        suggested_object_id="all_info_set",
        capabilities={ATTR_MIN_TEMP: 60, ATTR_MAX_TEMP: 70},
        supported_features=0,
        original_device_class="mock-device-class",
    )

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START, {})
    await hass.async_block_till_done()

    entity_id = "water_heater.simple"
    hass.states.async_set(entity_id, "off")
    state = hass.states.get(entity_id)
    assert state

    acc = Thermostat(hass, hk_driver, "WaterHeater", entity_id, 2, None)
    assert acc.category == 9
    assert acc.get_temperature_range(state) == (7, 35)
    assert set(acc.char_current_heat_cool.properties["ValidValues"].keys()) == {
        "Cool",
        "Heat",
        "Off",
    }

    entity_id = "water_heater.all_info_set"
    state = hass.states.get(entity_id)
    assert state

    acc = WaterHeater(hass, hk_driver, "WaterHeater", entity_id, 3, None)
    assert acc.category == 9
    assert acc.get_temperature_range(state) == (60.0, 70.0)
    assert set(acc.char_current_heat_cool.properties["ValidValues"].keys()) == {
        "Cool",
        "Heat",
        "Off",
    }