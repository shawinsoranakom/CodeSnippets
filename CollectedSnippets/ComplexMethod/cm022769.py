async def test_thermostat_hvac_modes_with_heat_only(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test if unsupported HVAC modes are deactivated in HomeKit and siri calls get converted to heat."""
    entity_id = "climate.test"

    hass.states.async_set(
        entity_id, HVACMode.HEAT, {ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.OFF]}
    )

    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()
    hap = acc.char_target_heat_cool.to_HAP()
    assert hap["valid-values"] == [HC_HEAT_COOL_OFF, HC_HEAT_COOL_HEAT]
    assert acc.char_target_heat_cool.allow_invalid_client_values is True
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_HEAT

    acc.char_target_heat_cool.set_value(HC_HEAT_COOL_HEAT)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_HEAT

    with pytest.raises(ValueError):
        acc.char_target_heat_cool.set_value(HC_HEAT_COOL_COOL)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_HEAT

    with pytest.raises(ValueError):
        acc.char_target_heat_cool.set_value(HC_HEAT_COOL_AUTO)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_HEAT

    char_target_heat_cool_iid = acc.char_target_heat_cool.to_HAP()[HAP_REPR_IID]
    call_set_hvac_mode = async_mock_service(hass, CLIMATE_DOMAIN, "set_hvac_mode")
    await hass.async_block_till_done()
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
                    HAP_REPR_VALUE: HC_HEAT_COOL_AUTO,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_hvac_mode
    assert call_set_hvac_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[0].data[ATTR_HVAC_MODE] == HVACMode.HEAT

    acc.char_target_heat_cool.client_update_value(HC_HEAT_COOL_OFF)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_OFF
    hass.states.async_set(
        entity_id, HVACMode.OFF, {ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.OFF]}
    )
    await hass.async_block_till_done()

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
                    HAP_REPR_VALUE: HC_HEAT_COOL_AUTO,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == HC_HEAT_COOL_HEAT