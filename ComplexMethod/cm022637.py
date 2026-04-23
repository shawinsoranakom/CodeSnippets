async def test_hygrostat_get_humidity_range(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if humidity range is evaluated correctly."""
    entity_id = "humidifier.test"

    hass.states.async_set(
        entity_id, STATE_OFF, {ATTR_MIN_HUMIDITY: 40, ATTR_MAX_HUMIDITY: 45}
    )
    await hass.async_block_till_done()
    acc = HumidifierDehumidifier(
        hass, hk_driver, "HumidifierDehumidifier", entity_id, 1, None
    )
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    # Set from HomeKit
    call_set_humidity = async_mock_service(
        hass, HUMIDIFIER_DOMAIN, SERVICE_SET_HUMIDITY
    )

    char_target_humidity_iid = acc.char_target_humidity.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_humidity_iid,
                    HAP_REPR_VALUE: 12.0,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_humidity[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_humidity[-1].data[ATTR_HUMIDITY] == 40.0
    assert acc.char_target_humidity.value == 40.0
    assert events[-1].data[ATTR_VALUE] == "RelativeHumidityHumidifierThreshold to 12.0%"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_humidity_iid,
                    HAP_REPR_VALUE: 80.0,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert call_set_humidity[-1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_humidity[-1].data[ATTR_HUMIDITY] == 45.0
    assert acc.char_target_humidity.value == 45.0
    assert events[-1].data[ATTR_VALUE] == "RelativeHumidityHumidifierThreshold to 80.0%"