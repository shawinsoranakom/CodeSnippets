async def test_thermostat_hvac_modes_with_heat_cool_only(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test if unsupported HVAC modes are deactivated in HomeKit and siri calls get converted to heat or cool."""
    entity_id = "climate.test"

    hass.states.async_set(
        entity_id,
        HVACMode.COOL,
        {
            ATTR_CURRENT_TEMPERATURE: 30,
            ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF],
        },
    )

    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()
    hap = acc.char_target_heat_cool.to_HAP()
    assert hap["valid-values"] == [
        HC_HEAT_COOL_OFF,
        HC_HEAT_COOL_HEAT,
        HC_HEAT_COOL_COOL,
    ]
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_COOL

    acc.char_target_heat_cool.set_value(HC_HEAT_COOL_COOL)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_COOL

    with pytest.raises(ValueError):
        acc.char_target_heat_cool.set_value(HC_HEAT_COOL_AUTO)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_COOL

    acc.char_target_heat_cool.set_value(HC_HEAT_COOL_HEAT)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_HEAT
    char_target_temp_iid = acc.char_target_temp.to_HAP()[HAP_REPR_IID]
    char_target_heat_cool_iid = acc.char_target_heat_cool.to_HAP()[HAP_REPR_IID]
    call_set_hvac_mode = async_mock_service(hass, CLIMATE_DOMAIN, "set_hvac_mode")
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
                    HAP_REPR_VALUE: HC_HEAT_COOL_AUTO,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_temp_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_hvac_mode
    assert call_set_hvac_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[0].data[ATTR_HVAC_MODE] == HVACMode.COOL
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
                    HAP_REPR_VALUE: HC_HEAT_COOL_AUTO,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_temp_iid,
                    HAP_REPR_VALUE: 200,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_hvac_mode
    assert call_set_hvac_mode[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[1].data[ATTR_HVAC_MODE] == HVACMode.HEAT