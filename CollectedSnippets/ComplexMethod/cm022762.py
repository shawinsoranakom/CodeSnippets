async def test_thermostat_humidity(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly with humidity."""
    entity_id = "climate.test"
    base_attrs = {ATTR_SUPPORTED_FEATURES: 4}
    # support_auto = True
    hass.states.async_set(entity_id, HVACMode.OFF, base_attrs)
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_target_humidity.value == 50
    assert acc.char_current_humidity.value == 50

    assert acc.char_target_humidity.properties[PROP_MIN_VALUE] == DEFAULT_MIN_HUMIDITY

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT_COOL,
        {**base_attrs, ATTR_HUMIDITY: 65, ATTR_CURRENT_HUMIDITY: 40},
    )
    await hass.async_block_till_done()
    assert acc.char_current_humidity.value == 40
    assert acc.char_target_humidity.value == 65

    hass.states.async_set(
        entity_id,
        HVACMode.COOL,
        {**base_attrs, ATTR_HUMIDITY: 35, ATTR_CURRENT_HUMIDITY: 70},
    )
    await hass.async_block_till_done()
    assert acc.char_current_humidity.value == 70
    assert acc.char_target_humidity.value == 35

    # Set from HomeKit
    call_set_humidity = async_mock_service(hass, CLIMATE_DOMAIN, "set_humidity")

    char_target_humidity_iid = acc.char_target_humidity.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_humidity_iid,
                    HAP_REPR_VALUE: 35,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_humidity[0]
    assert call_set_humidity[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_humidity[0].data[ATTR_HUMIDITY] == 35
    assert acc.char_target_humidity.value == 35
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == "35%"