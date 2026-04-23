async def test_thermostat_without_target_temp_only_range(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test a thermostat that only supports a range."""
    entity_id = "climate.test"
    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
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

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT_COOL,
        {
            **base_attrs,
            ATTR_TARGET_TEMP_HIGH: 22.0,
            ATTR_TARGET_TEMP_LOW: 20.0,
            ATTR_CURRENT_TEMPERATURE: 18.0,
            ATTR_HVAC_ACTION: HVACAction.HEATING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_heating_thresh_temp.value == 20.0
    assert acc.char_cooling_thresh_temp.value == 22.0
    assert acc.char_current_heat_cool.value == 1
    assert acc.char_target_heat_cool.value == 3
    assert acc.char_current_temp.value == 18.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.COOL,
        {
            **base_attrs,
            ATTR_TARGET_TEMP_HIGH: 23.0,
            ATTR_TARGET_TEMP_LOW: 19.0,
            ATTR_CURRENT_TEMPERATURE: 24.0,
            ATTR_HVAC_ACTION: HVACAction.COOLING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_heating_thresh_temp.value == 19.0
    assert acc.char_cooling_thresh_temp.value == 23.0
    assert acc.char_current_heat_cool.value == 2
    assert acc.char_target_heat_cool.value == 2
    assert acc.char_current_temp.value == 24.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.COOL,
        {
            **base_attrs,
            ATTR_TARGET_TEMP_HIGH: 23.0,
            ATTR_TARGET_TEMP_LOW: 19.0,
            ATTR_CURRENT_TEMPERATURE: 21.0,
            ATTR_HVAC_ACTION: HVACAction.IDLE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_heating_thresh_temp.value == 19.0
    assert acc.char_cooling_thresh_temp.value == 23.0
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 2
    assert acc.char_current_temp.value == 21.0
    assert acc.char_display_units.value == 0

    # Set from HomeKit
    call_set_temperature = async_mock_service(hass, CLIMATE_DOMAIN, "set_temperature")

    char_target_temp_iid = acc.char_target_temp.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_temp_iid,
                    HAP_REPR_VALUE: 17.0,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_temperature[0]
    assert call_set_temperature[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_temperature[0].data[ATTR_TARGET_TEMP_LOW] == 12.0
    assert call_set_temperature[0].data[ATTR_TARGET_TEMP_HIGH] == 17.0
    assert acc.char_target_temp.value == 17.0
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "CoolingThresholdTemperature to 17.0°C"

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            ATTR_TARGET_TEMP_HIGH: 23.0,
            ATTR_TARGET_TEMP_LOW: 19.0,
            ATTR_CURRENT_TEMPERATURE: 21.0,
            ATTR_HVAC_ACTION: HVACAction.IDLE,
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_heating_thresh_temp.value == 19.0
    assert acc.char_cooling_thresh_temp.value == 23.0
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 1
    assert acc.char_current_temp.value == 21.0
    assert acc.char_display_units.value == 0

    # Set from HomeKit
    call_set_temperature = async_mock_service(hass, CLIMATE_DOMAIN, "set_temperature")

    char_target_temp_iid = acc.char_target_temp.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_temp_iid,
                    HAP_REPR_VALUE: 27.0,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_temperature[0]
    assert call_set_temperature[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_temperature[0].data[ATTR_TARGET_TEMP_LOW] == 27.0
    assert call_set_temperature[0].data[ATTR_TARGET_TEMP_HIGH] == 32.0
    assert acc.char_target_temp.value == 27.0
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "HeatingThresholdTemperature to 27.0°C"