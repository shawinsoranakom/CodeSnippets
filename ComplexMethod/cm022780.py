async def test_thermostat_with_temp_clamps(hass: HomeAssistant, hk_driver) -> None:
    """Test that temperatures are clamped to valid values to prevent homekit crash."""
    entity_id = "climate.test"
    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        ATTR_HVAC_MODES: [HVACMode.HEAT_COOL, HVACMode.AUTO],
        ATTR_MAX_TEMP: 100,
        ATTR_MIN_TEMP: 50,
    }
    hass.states.async_set(
        entity_id,
        HVACMode.COOL,
        base_attrs,
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_cooling_thresh_temp.value == 50
    assert acc.char_heating_thresh_temp.value == 50

    assert acc.char_cooling_thresh_temp.properties[PROP_MAX_VALUE] == 100
    assert acc.char_cooling_thresh_temp.properties[PROP_MIN_VALUE] == 50
    assert acc.char_cooling_thresh_temp.properties[PROP_MIN_STEP] == 0.1
    assert acc.char_heating_thresh_temp.properties[PROP_MAX_VALUE] == 100
    assert acc.char_heating_thresh_temp.properties[PROP_MIN_VALUE] == 50
    assert acc.char_heating_thresh_temp.properties[PROP_MIN_STEP] == 0.1

    assert acc.char_target_heat_cool.value == 3

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT_COOL,
        {
            **base_attrs,
            ATTR_TARGET_TEMP_HIGH: 822.0,
            ATTR_TARGET_TEMP_LOW: 20.0,
            ATTR_CURRENT_TEMPERATURE: 9918.0,
            ATTR_HVAC_ACTION: HVACAction.HEATING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_heating_thresh_temp.value == 50.0
    assert acc.char_cooling_thresh_temp.value == 100.0
    assert acc.char_current_heat_cool.value == 1
    assert acc.char_target_heat_cool.value == 3
    assert acc.char_current_temp.value == 1000
    assert acc.char_display_units.value == 0