async def test_dehumidifier(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if dehumidifier accessory and HA are updated accordingly."""
    entity_id = "humidifier.test"

    hass.states.async_set(
        entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: HumidifierDeviceClass.DEHUMIDIFIER}
    )
    await hass.async_block_till_done()
    acc = HumidifierDehumidifier(
        hass, hk_driver, "HumidifierDehumidifier", entity_id, 1, None
    )
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 1
    assert acc.category == CATEGORY_HUMIDIFIER

    assert acc.char_current_humidifier_dehumidifier.value == 0
    assert acc.char_target_humidifier_dehumidifier.value == 2
    assert acc.char_current_humidity.value == 0
    assert acc.char_target_humidity.value == 45.0
    assert acc.char_active.value == 0

    assert acc.char_target_humidity.properties[PROP_MAX_VALUE] == DEFAULT_MAX_HUMIDITY
    assert acc.char_target_humidity.properties[PROP_MIN_VALUE] == DEFAULT_MIN_HUMIDITY
    assert acc.char_target_humidity.properties[PROP_MIN_STEP] == 1.0
    assert acc.char_target_humidifier_dehumidifier.properties[PROP_VALID_VALUES] == {
        "Dehumidifier": 2
    }
    assert acc.char_current_humidifier_dehumidifier.properties[PROP_VALID_VALUES] == {
        "Dehumidifying": 3,
        "Idle": 1,
        "Inactive": 0,
    }

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_HUMIDITY: 30, ATTR_DEVICE_CLASS: HumidifierDeviceClass.DEHUMIDIFIER},
    )
    await hass.async_block_till_done()
    assert acc.char_target_humidity.value == 30.0
    assert acc.char_current_humidifier_dehumidifier.value == 3
    assert acc.char_target_humidifier_dehumidifier.value == 2
    assert acc.char_active.value == 1

    hass.states.async_set(
        entity_id,
        STATE_OFF,
        {ATTR_HUMIDITY: 42, ATTR_DEVICE_CLASS: HumidifierDeviceClass.DEHUMIDIFIER},
    )
    await hass.async_block_till_done()
    assert acc.char_target_humidity.value == 42.0
    assert acc.char_current_humidifier_dehumidifier.value == 0
    assert acc.char_target_humidifier_dehumidifier.value == 2
    assert acc.char_active.value == 0

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
                    HAP_REPR_VALUE: 39.0,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    assert len(call_set_humidity) == 1
    assert call_set_humidity[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_humidity[0].data[ATTR_HUMIDITY] == 39.0
    assert acc.char_target_humidity.value == 39.0
    assert len(events) == 1
    assert (
        events[-1].data[ATTR_VALUE] == "RelativeHumidityDehumidifierThreshold to 39.0%"
    )