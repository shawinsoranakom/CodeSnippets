async def test_thermostat_with_fan_modes_with_auto(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test a thermostate with fan modes with an auto fan mode."""
    entity_id = "climate.test"
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE,
            ATTR_FAN_MODES: [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH],
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
    assert acc.ordered_fan_speeds == [FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    assert CHAR_ROTATION_SPEED in acc.fan_chars
    assert CHAR_TARGET_FAN_STATE in acc.fan_chars
    assert CHAR_SWING_MODE in acc.fan_chars
    assert CHAR_CURRENT_FAN_STATE in acc.fan_chars
    assert acc.char_speed.value == 100

    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE,
            ATTR_FAN_MODES: [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH],
            ATTR_SWING_MODES: [SWING_BOTH, SWING_OFF, SWING_HORIZONTAL],
            ATTR_HVAC_ACTION: HVACAction.IDLE,
            ATTR_FAN_MODE: FAN_LOW,
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
    assert acc.char_speed.value == pytest.approx(100 / 3)

    call_set_swing_mode = async_mock_service(
        hass, CLIMATE_DOMAIN, SERVICE_SET_SWING_MODE
    )
    char_swing_iid = acc.char_swing.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 0,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_set_swing_mode) == 1
    assert call_set_swing_mode[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_swing_mode[-1].data[ATTR_SWING_MODE] == SWING_OFF

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_set_swing_mode) == 2
    assert call_set_swing_mode[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_swing_mode[-1].data[ATTR_SWING_MODE] == SWING_BOTH

    call_set_fan_mode = async_mock_service(hass, CLIMATE_DOMAIN, SERVICE_SET_FAN_MODE)
    char_rotation_speed_iid = acc.char_speed.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_rotation_speed_iid,
                    HAP_REPR_VALUE: 100,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_set_fan_mode) == 1
    assert call_set_fan_mode[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_fan_mode[-1].data[ATTR_FAN_MODE] == FAN_HIGH

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_rotation_speed_iid,
                    HAP_REPR_VALUE: 100 / 3,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_set_fan_mode) == 2
    assert call_set_fan_mode[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_fan_mode[-1].data[ATTR_FAN_MODE] == FAN_LOW

    char_active_iid = acc.char_active.to_HAP()[HAP_REPR_IID]
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 0,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert acc.char_active.value == 1

    char_target_fan_state_iid = acc.char_target_fan_state.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_fan_state_iid,
                    HAP_REPR_VALUE: 1,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_set_fan_mode) == 3
    assert call_set_fan_mode[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_fan_mode[-1].data[ATTR_FAN_MODE] == FAN_AUTO

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_fan_state_iid,
                    HAP_REPR_VALUE: 0,
                }
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_set_fan_mode) == 4
    assert call_set_fan_mode[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_fan_mode[-1].data[ATTR_FAN_MODE] == FAN_MEDIUM