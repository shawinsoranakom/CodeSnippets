async def test_thermostat_fahrenheit(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "climate.test"
    hass.config.units = US_CUSTOMARY_SYSTEM

    # support_ = True
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        },
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)
    acc.run()
    await hass.async_block_till_done()

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT_COOL,
        {
            ATTR_TARGET_TEMP_HIGH: 75.2,
            ATTR_TARGET_TEMP_LOW: 68.1,
            ATTR_TEMPERATURE: 71.6,
            ATTR_CURRENT_TEMPERATURE: 73.4,
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        },
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state
    assert acc.get_temperature_range(state) == (7.0, 35.0)
    assert acc.char_heating_thresh_temp.value == 20.1
    assert acc.char_cooling_thresh_temp.value == 24.0
    assert acc.char_current_temp.value == 23.0
    assert acc.char_target_temp.value == 22.0
    assert acc.char_display_units.value == 1

    # Set from HomeKit
    call_set_temperature = async_mock_service(hass, CLIMATE_DOMAIN, "set_temperature")

    char_cooling_thresh_temp_iid = acc.char_cooling_thresh_temp.to_HAP()[HAP_REPR_IID]
    char_heating_thresh_temp_iid = acc.char_heating_thresh_temp.to_HAP()[HAP_REPR_IID]
    char_target_temp_iid = acc.char_target_temp.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_cooling_thresh_temp_iid,
                    HAP_REPR_VALUE: 23,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_temperature[0]
    assert call_set_temperature[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_temperature[0].data[ATTR_TARGET_TEMP_HIGH] == 73.4
    assert call_set_temperature[0].data[ATTR_TARGET_TEMP_LOW] == 68.18
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "CoolingThresholdTemperature to 23°C"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_heating_thresh_temp_iid,
                    HAP_REPR_VALUE: 22,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_temperature[1]
    assert call_set_temperature[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_temperature[1].data[ATTR_TARGET_TEMP_HIGH] == 73.4
    assert call_set_temperature[1].data[ATTR_TARGET_TEMP_LOW] == 71.6
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "HeatingThresholdTemperature to 22°C"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_temp_iid,
                    HAP_REPR_VALUE: 24.0,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_set_temperature[2]
    assert call_set_temperature[2].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_temperature[2].data[ATTR_TEMPERATURE] == 75.2
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] == "TargetTemperature to 24.0°C"