async def test_thermostat_with_no_off_after_recheck(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test if a thermostat that is not ready when we first see it that actually does not have off."""
    entity_id = "climate.test"

    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        ATTR_HVAC_MODES: [],
    }
    # support_auto = True
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

    assert acc.char_cooling_thresh_temp.value == 23.0
    assert acc.char_heating_thresh_temp.value == 19.0

    assert acc.char_cooling_thresh_temp.properties[PROP_MAX_VALUE] == DEFAULT_MAX_TEMP
    assert acc.char_cooling_thresh_temp.properties[PROP_MIN_VALUE] == 7.0
    assert acc.char_cooling_thresh_temp.properties[PROP_MIN_STEP] == 0.1
    assert acc.char_heating_thresh_temp.properties[PROP_MAX_VALUE] == DEFAULT_MAX_TEMP
    assert acc.char_heating_thresh_temp.properties[PROP_MIN_VALUE] == 7.0
    assert acc.char_heating_thresh_temp.properties[PROP_MIN_STEP] == 0.1

    assert acc.char_target_heat_cool.value == 2

    # Verify reload when modes change out from under us
    with patch.object(acc, "async_reload") as mock_reload:
        hass.states.async_set(
            entity_id,
            HVACMode.HEAT_COOL,
            {
                **base_attrs,
                ATTR_TARGET_TEMP_HIGH: 22.0,
                ATTR_TARGET_TEMP_LOW: 20.0,
                ATTR_CURRENT_TEMPERATURE: 18.0,
                ATTR_HVAC_ACTION: HVACAction.HEATING,
                ATTR_HVAC_MODES: [HVACMode.HEAT_COOL, HVACMode.AUTO],
            },
        )
        await hass.async_block_till_done()
        assert mock_reload.called