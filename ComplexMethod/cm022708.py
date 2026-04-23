async def test_fan_set_all_one_shot(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test fan with speed."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.DIRECTION,
            ATTR_PERCENTAGE: 0,
            ATTR_OSCILLATING: False,
            ATTR_DIRECTION: DIRECTION_FORWARD,
        },
    )
    await hass.async_block_till_done()
    acc = Fan(hass, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    # Initial value can be anything but 0. If it is 0, it might cause HomeKit to set the
    # speed to 100 when turning on a fan on a freshly booted up server.
    assert acc.char_speed.value != 0
    acc.run()
    await hass.async_block_till_done()

    hass.states.async_set(
        entity_id,
        STATE_OFF,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.DIRECTION,
            ATTR_PERCENTAGE: 0,
            ATTR_OSCILLATING: False,
            ATTR_DIRECTION: DIRECTION_FORWARD,
        },
    )
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_OFF

    # Set from HomeKit
    call_set_percentage = async_mock_service(hass, FAN_DOMAIN, "set_percentage")
    call_oscillate = async_mock_service(hass, FAN_DOMAIN, "oscillate")
    call_set_direction = async_mock_service(hass, FAN_DOMAIN, "set_direction")
    call_turn_on = async_mock_service(hass, FAN_DOMAIN, "turn_on")
    call_turn_off = async_mock_service(hass, FAN_DOMAIN, "turn_off")

    char_active_iid = acc.char_active.to_HAP()[HAP_REPR_IID]
    char_direction_iid = acc.char_direction.to_HAP()[HAP_REPR_IID]
    char_swing_iid = acc.char_swing.to_HAP()[HAP_REPR_IID]
    char_speed_iid = acc.char_speed.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_speed_iid,
                    HAP_REPR_VALUE: 42,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert not call_turn_on
    assert call_set_percentage[0]
    assert call_set_percentage[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_percentage[0].data[ATTR_PERCENTAGE] == 42
    assert call_oscillate[0]
    assert call_oscillate[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_oscillate[0].data[ATTR_OSCILLATING] is True
    assert call_set_direction[0]
    assert call_set_direction[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_direction[0].data[ATTR_DIRECTION] == DIRECTION_REVERSE
    assert len(events) == 3

    assert events[0].data[ATTR_VALUE] is True
    assert events[1].data[ATTR_VALUE] == DIRECTION_REVERSE
    assert events[2].data[ATTR_VALUE] == 42

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED
            | FanEntityFeature.OSCILLATE
            | FanEntityFeature.DIRECTION,
            ATTR_PERCENTAGE: 0,
            ATTR_OSCILLATING: False,
            ATTR_DIRECTION: DIRECTION_FORWARD,
        },
    )
    await hass.async_block_till_done()

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_speed_iid,
                    HAP_REPR_VALUE: 42,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    # Turn on should not be called if its already on
    # and we set a fan speed
    await hass.async_block_till_done()
    assert len(events) == 6
    assert call_set_percentage[1]
    assert call_set_percentage[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_percentage[1].data[ATTR_PERCENTAGE] == 42
    assert call_oscillate[1]
    assert call_oscillate[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_oscillate[1].data[ATTR_OSCILLATING] is True
    assert call_set_direction[1]
    assert call_set_direction[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_direction[1].data[ATTR_DIRECTION] == DIRECTION_REVERSE

    assert events[-3].data[ATTR_VALUE] is True
    assert events[-2].data[ATTR_VALUE] == DIRECTION_REVERSE
    assert events[-1].data[ATTR_VALUE] == 42

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_active_iid,
                    HAP_REPR_VALUE: 0,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_speed_iid,
                    HAP_REPR_VALUE: 42,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_swing_iid,
                    HAP_REPR_VALUE: 1,
                },
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_direction_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()

    assert len(events) == 7
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(call_set_percentage) == 2
    assert len(call_oscillate) == 2
    assert len(call_set_direction) == 2