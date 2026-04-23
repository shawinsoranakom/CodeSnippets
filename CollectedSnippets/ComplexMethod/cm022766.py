async def test_thermostat_hvac_modes_with_auto_heat_cool(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test we get heat cool over auto."""
    entity_id = "climate.test"

    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_HVAC_MODES: [
                HVACMode.HEAT_COOL,
                HVACMode.AUTO,
                HVACMode.HEAT,
                HVACMode.OFF,
            ]
        },
    )
    call_set_hvac_mode = async_mock_service(hass, CLIMATE_DOMAIN, "set_hvac_mode")
    await hass.async_block_till_done()

    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()
    hap = acc.char_target_heat_cool.to_HAP()
    assert hap["valid-values"] == [0, 1, 3]
    assert acc.char_target_heat_cool.value == 0

    acc.char_target_heat_cool.set_value(3)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 3

    acc.char_target_heat_cool.set_value(1)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 1

    with pytest.raises(ValueError):
        acc.char_target_heat_cool.set_value(2)
    await hass.async_block_till_done()
    assert acc.char_target_heat_cool.value == 1

    char_target_heat_cool_iid = acc.char_target_heat_cool.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
                    HAP_REPR_VALUE: 3,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_hvac_mode
    assert call_set_hvac_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_hvac_mode[0].data[ATTR_HVAC_MODE] == HVACMode.HEAT_COOL
    assert acc.char_target_heat_cool.value == 3