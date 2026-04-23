async def test_thermostat_handles_unknown_state(hass: HomeAssistant, hk_driver) -> None:
    """Test a thermostat can handle unknown state."""
    entity_id = "climate.test"
    attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE,
        ATTR_MIN_TEMP: 44.6,
        ATTR_MAX_TEMP: 95,
        ATTR_PRESET_MODES: ["home", "away"],
        ATTR_TEMPERATURE: 67,
        ATTR_TARGET_TEMP_HIGH: None,
        ATTR_TARGET_TEMP_LOW: None,
        ATTR_FAN_MODE: FAN_AUTO,
        ATTR_FAN_MODES: None,
        ATTR_HVAC_ACTION: HVACAction.IDLE,
        ATTR_PRESET_MODE: "home",
        ATTR_FRIENDLY_NAME: "Rec Room",
        ATTR_HVAC_MODES: [
            HVACMode.OFF,
            HVACMode.HEAT,
        ],
    }

    call_set_hvac_mode = async_mock_service(hass, CLIMATE_DOMAIN, "set_hvac_mode")
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        attrs,
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()
    heat_cool_char: Characteristic = acc.char_target_heat_cool

    assert heat_cool_char.value == HC_HEAT_COOL_OFF
    assert acc.available is True
    hass.states.async_set(
        entity_id,
        STATE_UNKNOWN,
        attrs,
    )
    await hass.async_block_till_done()

    assert heat_cool_char.value == HC_HEAT_COOL_OFF
    assert acc.available is True

    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        attrs,
    )
    await hass.async_block_till_done()
    assert heat_cool_char.value == HC_HEAT_COOL_OFF
    assert acc.available is True

    hass.states.async_set(
        entity_id,
        STATE_UNAVAILABLE,
        attrs,
    )
    await hass.async_block_till_done()

    assert heat_cool_char.value == HC_HEAT_COOL_OFF
    assert acc.available is False

    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        attrs,
    )
    await hass.async_block_till_done()

    assert heat_cool_char.value == HC_HEAT_COOL_OFF
    assert acc.available is True
    hass.states.async_set(
        entity_id,
        STATE_UNAVAILABLE,
        attrs,
    )
    await hass.async_block_till_done()

    assert heat_cool_char.value == HC_HEAT_COOL_OFF
    assert acc.available is False

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: heat_cool_char.to_HAP()[HAP_REPR_IID],
                    HAP_REPR_VALUE: HC_HEAT_COOL_HEAT,
                }
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert heat_cool_char.value == HC_HEAT_COOL_HEAT
    assert acc.available is False
    assert call_set_hvac_mode
    assert call_set_hvac_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[0].data[ATTR_HVAC_MODE] == HVACMode.HEAT

    hass.states.async_set(
        entity_id,
        STATE_UNKNOWN,
        attrs,
    )
    await hass.async_block_till_done()

    assert heat_cool_char.value == HC_HEAT_COOL_HEAT
    assert acc.available is True

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: heat_cool_char.to_HAP()[HAP_REPR_IID],
                    HAP_REPR_VALUE: HC_HEAT_COOL_HEAT,
                }
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert heat_cool_char.value == HC_HEAT_COOL_HEAT
    assert acc.available is True
    assert call_set_hvac_mode
    assert call_set_hvac_mode[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[1].data[ATTR_HVAC_MODE] == HVACMode.HEAT