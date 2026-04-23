async def test_thermostat_hvac_modes_with_auto_only(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test if unsupported HVAC modes are deactivated in HomeKit."""
    entity_id = "climate.test"

    hass.states.async_set(
        entity_id, HVACMode.AUTO, {ATTR_HVAC_MODES: [HVACMode.AUTO, HVACMode.OFF]}
    )

    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()
    hap = acc.char_target_heat_cool.to_HAP()
    assert hap["valid-values"] == [0, 3]
    assert acc.char_target_heat_cool.value == 3

    acc.char_target_heat_cool.set_value(3)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 3

    with pytest.raises(ValueError):
        acc.char_target_heat_cool.set_value(1)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 3

    with pytest.raises(ValueError):
        acc.char_target_heat_cool.set_value(2)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 3

    char_target_heat_cool_iid = acc.char_target_heat_cool.to_HAP()[HAP_REPR_IID]
    call_set_hvac_mode = async_mock_service(hass, CLIMATE_DOMAIN, "set_hvac_mode")
    await hass.async_block_till_done()
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
                    HAP_REPR_VALUE: HC_HEAT_COOL_HEAT,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_hvac_mode
    assert call_set_hvac_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[0].data[ATTR_HVAC_MODE] == HVACMode.AUTO