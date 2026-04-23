async def test_fan_direction(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test fan with direction."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.DIRECTION,
            ATTR_DIRECTION: DIRECTION_FORWARD,
        },
    )
    await hass.async_block_till_done()
    acc = Fan(hass, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_direction.value == 0

    acc.run()
    await hass.async_block_till_done()
    assert acc.char_direction.value == 0

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.DIRECTION,
            ATTR_DIRECTION: DIRECTION_REVERSE,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_direction.value == 1

    # Set from HomeKit
    call_set_direction = async_mock_service(hass, FAN_DOMAIN, "set_direction")

    char_direction_iid = acc.char_direction.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_set_direction[0]
    assert call_set_direction[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_direction[0].data[ATTR_DIRECTION] == DIRECTION_FORWARD
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == DIRECTION_FORWARD

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    acc.char_direction.client_update_value(1)
    await hass.async_block_till_done()
    assert call_set_direction[1]
    assert call_set_direction[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_direction[1].data[ATTR_DIRECTION] == DIRECTION_REVERSE
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == DIRECTION_REVERSE