async def test_thermostat_reversed_min_max(hass: HomeAssistant, hk_driver) -> None:
    """Test reversed min/max temperatures."""
    entity_id = "climate.test"
    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        ATTR_HVAC_MODES: [
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
            HVACMode.FAN_ONLY,
            HVACMode.COOL,
            HVACMode.OFF,
            HVACMode.AUTO,
        ],
        ATTR_MAX_TEMP: DEFAULT_MAX_TEMP,
        ATTR_MIN_TEMP: DEFAULT_MIN_TEMP,
    }
    # support_auto = True
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        base_attrs,
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_cooling_thresh_temp.value == 23.0
    assert acc.char_heating_thresh_temp.value == 19.0

    assert acc.char_cooling_thresh_temp.properties[PROP_MAX_VALUE] == DEFAULT_MAX_TEMP
    assert acc.char_cooling_thresh_temp.properties[PROP_MIN_VALUE] == 7.0
    assert acc.char_cooling_thresh_temp.properties[PROP_MIN_STEP] == 0.1
    assert acc.char_heating_thresh_temp.properties[PROP_MAX_VALUE] == DEFAULT_MAX_TEMP
    assert acc.char_heating_thresh_temp.properties[PROP_MIN_VALUE] == 7.0
    assert acc.char_heating_thresh_temp.properties[PROP_MIN_STEP] == 0.1