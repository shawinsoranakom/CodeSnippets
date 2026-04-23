async def test_thermostat(hass: HomeAssistant, hk_driver, events: list[Event]) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "climate.test"
    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE,
        ATTR_HVAC_MODES: [
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
            HVACMode.FAN_ONLY,
            HVACMode.COOL,
            HVACMode.OFF,
            HVACMode.AUTO,
        ],
    }

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

    assert acc.aid == 1
    assert acc.category == 9  # Thermostat

    state = hass.states.get(entity_id)
    assert state
    assert acc.get_temperature_range(state) == (7.0, 35.0)
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 0
    assert acc.char_current_temp.value == 21.0
    assert acc.char_target_temp.value == 21.0
    assert acc.char_display_units.value == 0
    assert acc.char_cooling_thresh_temp is None
    assert acc.char_heating_thresh_temp is None
    assert acc.char_target_humidity is None
    assert acc.char_current_humidity is None

    assert acc.char_target_temp.properties[PROP_MAX_VALUE] == DEFAULT_MAX_TEMP
    assert acc.char_target_temp.properties[PROP_MIN_VALUE] == 7.0
    assert acc.char_target_temp.properties[PROP_MIN_STEP] == 0.1

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.2,
            ATTR_CURRENT_TEMPERATURE: 17.8,
            ATTR_HVAC_ACTION: HVACAction.HEATING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.2
    assert acc.char_current_heat_cool.value == 1
    assert acc.char_target_heat_cool.value == 1
    assert acc.char_current_temp.value == 17.8
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.0,
            ATTR_CURRENT_TEMPERATURE: 23.0,
            ATTR_HVAC_ACTION: HVACAction.IDLE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.0
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 1
    assert acc.char_current_temp.value == 23.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.2,
            ATTR_CURRENT_TEMPERATURE: 17.8,
            ATTR_HVAC_ACTION: HVACAction.PREHEATING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.2
    assert acc.char_current_heat_cool.value == 1
    assert acc.char_target_heat_cool.value == 1
    assert acc.char_current_temp.value == 17.8
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.2,
            ATTR_CURRENT_TEMPERATURE: 17.8,
            ATTR_HVAC_ACTION: HVACAction.DEFROSTING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.2
    assert acc.char_current_heat_cool.value == 1
    assert acc.char_target_heat_cool.value == 1
    assert acc.char_current_temp.value == 17.8
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.FAN_ONLY,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 20.0,
            ATTR_CURRENT_TEMPERATURE: 25.0,
            ATTR_HVAC_ACTION: HVACAction.COOLING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 20.0
    assert acc.char_current_heat_cool.value == 2
    assert acc.char_target_heat_cool.value == 2
    assert acc.char_current_temp.value == 25.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.COOL,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 20.0,
            ATTR_CURRENT_TEMPERATURE: 19.0,
            ATTR_HVAC_ACTION: HVACAction.IDLE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 20.0
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 2
    assert acc.char_current_temp.value == 19.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {**base_attrs, ATTR_TEMPERATURE: 22.0, ATTR_CURRENT_TEMPERATURE: 18.0},
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.0
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 0
    assert acc.char_current_temp.value == 18.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.AUTO,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.0,
            ATTR_CURRENT_TEMPERATURE: 18.0,
            ATTR_HVAC_ACTION: HVACAction.HEATING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.0
    assert acc.char_current_heat_cool.value == 1
    assert acc.char_target_heat_cool.value == 3
    assert acc.char_current_temp.value == 18.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT_COOL,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.0,
            ATTR_CURRENT_TEMPERATURE: 25.0,
            ATTR_HVAC_ACTION: HVACAction.COOLING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.0
    assert acc.char_current_heat_cool.value == 2
    assert acc.char_target_heat_cool.value == 3
    assert acc.char_current_temp.value == 25.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.AUTO,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.0,
            ATTR_CURRENT_TEMPERATURE: 22.0,
            ATTR_HVAC_ACTION: HVACAction.IDLE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.0
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 3
    assert acc.char_current_temp.value == 22.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.FAN_ONLY,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.0,
            ATTR_CURRENT_TEMPERATURE: 22.0,
            ATTR_HVAC_ACTION: HVACAction.FAN,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.0
    assert acc.char_current_heat_cool.value == 2
    assert acc.char_target_heat_cool.value == 2
    assert acc.char_current_temp.value == 22.0
    assert acc.char_display_units.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.DRY,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 22.0,
            ATTR_CURRENT_TEMPERATURE: 22.0,
            ATTR_HVAC_ACTION: HVACAction.DRYING,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_temp.value == 22.0
    assert acc.char_current_heat_cool.value == 2
    assert acc.char_target_heat_cool.value == 2
    assert acc.char_current_temp.value == 22.0
    assert acc.char_display_units.value == 0

    # Set from HomeKit
    call_set_temperature = async_mock_service(hass, CLIMATE_DOMAIN, "set_temperature")
    call_set_hvac_mode = async_mock_service(hass, CLIMATE_DOMAIN, "set_hvac_mode")

    char_target_temp_iid = acc.char_target_temp.to_HAP()[HAP_REPR_IID]
    char_heat_cool_iid = acc.char_target_heat_cool.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_temp_iid,
                    HAP_REPR_VALUE: 19.0,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_set_temperature
    assert call_set_temperature[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_temperature[0].data[ATTR_TEMPERATURE] == 19.0
    assert acc.char_target_temp.value == 19.0
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "TargetTemperature to 19.0°C"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_heat_cool_iid,
                    HAP_REPR_VALUE: 2,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert not call_set_hvac_mode

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_heat_cool_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_set_hvac_mode
    assert call_set_hvac_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[0].data[ATTR_HVAC_MODE] == HVACMode.HEAT
    assert acc.char_target_heat_cool.value == 1
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "TargetHeatingCoolingState to 1"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_heat_cool_iid,
                    HAP_REPR_VALUE: 3,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_set_hvac_mode
    assert call_set_hvac_mode[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[1].data[ATTR_HVAC_MODE] == HVACMode.HEAT_COOL
    assert acc.char_target_heat_cool.value == 3
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] == "TargetHeatingCoolingState to 3"