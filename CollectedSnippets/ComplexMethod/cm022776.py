async def test_water_heater_fahrenheit(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are update accordingly."""
    entity_id = "water_heater.test"
    hass.config.units = US_CUSTOMARY_SYSTEM

    hass.states.async_set(entity_id, HVACMode.HEAT)
    await hass.async_block_till_done()
    acc = WaterHeater(hass, hk_driver, "WaterHeater", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    hass.states.async_set(entity_id, HVACMode.HEAT, {ATTR_TEMPERATURE: 131})
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 55.0
    assert acc.char_current_temp.value == 50
    assert acc.char_display_units.value == 1

    # Set from HomeKit
    call_set_temperature = async_mock_service(
        hass, WATER_HEATER_DOMAIN, "set_temperature"
    )

    acc.char_target_temp.client_update_value(60)
    await hass.async_block_till_done()
    assert call_set_temperature
    assert call_set_temperature[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_temperature[0].data[ATTR_TEMPERATURE] == 140.0
    assert acc.char_target_temp.value == 60.0
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "140.0°F"