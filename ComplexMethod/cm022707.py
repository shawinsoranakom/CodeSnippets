async def test_fan_speed(hass: HomeAssistant, hk_driver, events: list[Event]) -> None:
    """Test fan with speed."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED,
            ATTR_PERCENTAGE: 0,
            ATTR_PERCENTAGE_STEP: 25,
        },
    )
    await hass.async_block_till_done()
    acc = Fan(hass, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    # Initial value can be anything but 0. If it is 0, it might cause HomeKit to set the
    # speed to 100 when turning on a fan on a freshly booted up server.
    assert acc.char_speed.value != 0
    assert acc.char_speed.properties[PROP_MIN_STEP] == 25

    acc.run()
    await hass.async_block_till_done()

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_PERCENTAGE_STEP: 25,
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED,
            ATTR_PERCENTAGE: 100,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_speed.value == 100

    # Set from HomeKit
    call_set_percentage = async_mock_service(hass, FAN_DOMAIN, "set_percentage")

    char_speed_iid = acc.char_speed.to_HAP()[HAP_REPR_IID]
    char_active_iid = acc.char_active.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_speed_iid,
                    HAP_REPR_VALUE: 42,
                },
            ]
        },
        "mock_addr",
    )
    acc.char_speed.client_update_value(42)
    await hass.async_block_till_done()
    assert acc.char_speed.value == 50
    assert acc.char_active.value == 1

    assert call_set_percentage[0]
    assert call_set_percentage[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_percentage[0].data[ATTR_PERCENTAGE] == 42
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == 42

    # Verify speed is preserved from off to on
    hass.states.async_set(
        entity_id,
        STATE_OFF,
        {
            ATTR_PERCENTAGE_STEP: 25,
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED,
            ATTR_PERCENTAGE: 42,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_speed.value == 50
    assert acc.char_active.value == 0

    call_turn_on = async_mock_service(hass, FAN_DOMAIN, "turn_on")

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
    assert acc.char_speed.value == 50
    assert acc.char_active.value == 1

    assert call_turn_on[0]
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id