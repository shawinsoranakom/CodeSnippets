async def test_fan_single_preset_mode(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test fan with a single preset mode."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED,
            ATTR_PERCENTAGE: 42,
            ATTR_PRESET_MODE: "smart",
            ATTR_PRESET_MODES: ["smart"],
        },
    )
    await hass.async_block_till_done()
    acc = Fan(hass, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_target_fan_state.value == 1

    acc.run()
    await hass.async_block_till_done()

    # Set from HomeKit
    call_set_preset_mode = async_mock_service(hass, FAN_DOMAIN, "set_preset_mode")
    call_turn_on = async_mock_service(hass, FAN_DOMAIN, "turn_on")

    char_target_fan_state_iid = acc.char_target_fan_state.to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_fan_state_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_turn_on[0]
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_turn_on[0].data[ATTR_PERCENTAGE] == 42
    assert len(events) == 1
    assert events[-1].data["service"] == "turn_on"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_fan_state_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_set_preset_mode[0]
    assert call_set_preset_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_preset_mode[0].data[ATTR_PRESET_MODE] == "smart"
    assert events[-1].data["service"] == "set_preset_mode"
    assert len(events) == 2

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED,
            ATTR_PERCENTAGE: 42,
            ATTR_PRESET_MODE: None,
            ATTR_PRESET_MODES: ["smart"],
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_fan_state.value == 0