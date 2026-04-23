async def test_thermostat_power_state(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "climate.test"
    base_attrs = {
        ATTR_SUPPORTED_FEATURES: 4096,
        ATTR_TEMPERATURE: 23.0,
        ATTR_CURRENT_TEMPERATURE: 18.0,
        ATTR_HVAC_ACTION: HVACAction.HEATING,
        ATTR_HVAC_MODES: [
            HVACMode.HEAT_COOL,
            HVACMode.COOL,
            HVACMode.AUTO,
            HVACMode.HEAT,
            HVACMode.OFF,
        ],
    }
    # SUPPORT_ON_OFF = True
    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        base_attrs,
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_current_heat_cool.value == 1
    assert acc.char_target_heat_cool.value == 1

    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 23.0,
            ATTR_CURRENT_TEMPERATURE: 18.0,
            ATTR_HVAC_ACTION: HVACAction.IDLE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 0

    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            **base_attrs,
            ATTR_TEMPERATURE: 23.0,
            ATTR_CURRENT_TEMPERATURE: 18.0,
            ATTR_HVAC_ACTION: HVACAction.IDLE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_heat_cool.value == 0
    assert acc.char_target_heat_cool.value == 0

    # Set from HomeKit
    call_set_hvac_mode = async_mock_service(hass, CLIMATE_DOMAIN, "set_hvac_mode")

    char_target_heat_cool_iid = acc.char_target_heat_cool.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
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
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "TargetHeatingCoolingState to 1"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
                    HAP_REPR_VALUE: 2,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_hvac_mode
    assert call_set_hvac_mode[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[1].data[ATTR_HVAC_MODE] == HVACMode.COOL
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == "TargetHeatingCoolingState to 2"
    assert acc.char_target_heat_cool.value == 2