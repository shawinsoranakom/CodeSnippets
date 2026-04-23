async def test_fan_basic(hass: HomeAssistant, hk_driver, events: list[Event]) -> None:
    """Test fan with char state."""
    entity_id = "fan.demo"

    hass.states.async_set(entity_id, STATE_ON, {ATTR_SUPPORTED_FEATURES: 0})
    await hass.async_block_till_done()
    acc = Fan(hass, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.aid == 1
    assert acc.category == 3  # Fan
    assert acc.char_active.value == 1

    # If there are no speed_list values, then HomeKit speed is unsupported
    assert acc.char_speed is None

    acc.run()
    await hass.async_block_till_done()
    assert acc.char_active.value == 1

    hass.states.async_set(entity_id, STATE_OFF, {ATTR_SUPPORTED_FEATURES: 0})
    await hass.async_block_till_done()
    assert acc.char_active.value == 0

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert acc.char_active.value == 0

    hass.states.async_remove(entity_id)
    await hass.async_block_till_done()
    assert acc.char_active.value == 0

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, FAN_DOMAIN, "turn_on")
    call_turn_off = async_mock_service(hass, FAN_DOMAIN, "turn_off")

    char_active_iid = acc.char_active.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    hass.states.async_set(entity_id, STATE_ON)
    await hass.async_block_till_done()

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None