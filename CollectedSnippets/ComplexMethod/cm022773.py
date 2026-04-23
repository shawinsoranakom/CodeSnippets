async def test_water_heater(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "water_heater.test"

    hass.states.async_set(entity_id, HVACMode.HEAT)
    await hass.async_block_till_done()
    acc = WaterHeater(hass, hk_driver, "WaterHeater", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 9  # Thermostat

    assert acc.char_current_heat_cool.value == 1  # Heat
    assert acc.char_target_heat_cool.value == 1  # Heat
    assert acc.char_current_temp.value == 50.0
    assert acc.char_target_temp.value == 50.0
    assert acc.char_display_units.value == 0

    assert (
        acc.char_target_temp.properties[PROP_MAX_VALUE] == DEFAULT_MAX_TEMP_WATER_HEATER
    )
    assert (
        acc.char_target_temp.properties[PROP_MIN_VALUE] == DEFAULT_MIN_TEMP_WATER_HEATER
    )
    assert acc.char_target_temp.properties[PROP_MIN_STEP] == 0.1

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            ATTR_HVAC_MODE: HVACMode.HEAT,
            ATTR_TEMPERATURE: 56.0,
            ATTR_CURRENT_TEMPERATURE: 35.0,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 56.0
    assert acc.char_current_temp.value == 35.0
    assert acc.char_target_heat_cool.value == 1
    assert acc.char_current_heat_cool.value == 1
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id, HVACMode.HEAT_COOL, {ATTR_HVAC_MODE: HVACMode.HEAT_COOL}
    )
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 1
    assert acc.char_current_heat_cool.value == 1

    # Set from HomeKit
    call_set_temperature = async_mock_service(
        hass, WATER_HEATER_DOMAIN, "set_temperature"
    )

    acc.char_target_temp.client_update_value(52.0)
    await hass.async_block_till_done()
    assert call_set_temperature
    assert call_set_temperature[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_temperature[0].data[ATTR_TEMPERATURE] == 52.0
    assert acc.char_target_temp.value == 52.0
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == f"52.0{UnitOfTemperature.CELSIUS}"

    acc.char_target_heat_cool.client_update_value(1)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 1

    with pytest.raises(ValueError):
        acc.char_target_heat_cool.set_value(3)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 1