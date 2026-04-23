async def test_fan_oscillate(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test fan with oscillate."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_FEATURES: FanEntityFeature.OSCILLATE, ATTR_OSCILLATING: False},
    )
    await hass.async_block_till_done()
    acc = Fan(hass, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_swing.value == 0

    acc.run()
    await hass.async_block_till_done()
    assert acc.char_swing.value == 0

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {ATTR_SUPPORTED_FEATURES: FanEntityFeature.OSCILLATE, ATTR_OSCILLATING: True},
    )
    await hass.async_block_till_done()
    assert acc.char_swing.value == 1

    # Set from HomeKit
    call_oscillate = async_mock_service(hass, FAN_DOMAIN, "oscillate")

    char_swing_iid = acc.char_swing.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    acc.char_swing.client_update_value(0)
    await hass.async_block_till_done()
    assert call_oscillate[0]
    assert call_oscillate[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_oscillate[0].data[ATTR_OSCILLATING] is False
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is False

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    acc.char_swing.client_update_value(1)
    await hass.async_block_till_done()
    assert call_oscillate[1]
    assert call_oscillate[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_oscillate[1].data[ATTR_OSCILLATING] is True
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is True