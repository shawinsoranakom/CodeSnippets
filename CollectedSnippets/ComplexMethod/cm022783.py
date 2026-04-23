async def test_thermostat_with_fan_modes_set_to_none(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test a thermostate with fan modes set to None."""
    entity_id = "climate.test"
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE,
            ATTR_FAN_MODES: None,
            ATTR_SWING_MODES: [SWING_BOTH, SWING_OFF, SWING_HORIZONTAL],
            ATTR_HVAC_ACTION: HVACAction.IDLE,
            ATTR_FAN_MODE: FAN_AUTO,
            ATTR_SWING_MODE: SWING_BOTH,
            ATTR_HVAC_MODES: [
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
                HVACMode.FAN_ONLY,
                HVACMode.COOL,
                HVACMode.OFF,
                HVACMode.AUTO,
            ],
        },
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_cooling_thresh_temp.value == 23.0
    assert acc.char_heating_thresh_temp.value == 19.0
    assert acc.ordered_fan_speeds == []
    assert CHAR_ROTATION_SPEED not in acc.fan_chars
    assert CHAR_TARGET_FAN_STATE not in acc.fan_chars
    assert CHAR_SWING_MODE in acc.fan_chars
    assert CHAR_CURRENT_FAN_STATE in acc.fan_chars