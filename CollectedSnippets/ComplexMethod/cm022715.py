async def test_air_purifier_single_preset_mode(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test air purifier with a single preset mode."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED,
            ATTR_PERCENTAGE: 42,
            ATTR_PRESET_MODE: "auto",
            ATTR_PRESET_MODES: ["auto"],
        },
    )
    await hass.async_block_till_done()
    acc = AirPurifier(hass, hk_driver, "Air Purifier", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.char_target_air_purifier_state.value == TARGET_STATE_AUTO

    acc.run()
    await hass.async_block_till_done()

    # Set from HomeKit
    call_set_preset_mode = async_mock_service(hass, FAN_DOMAIN, "set_preset_mode")
    call_set_percentage = async_mock_service(hass, FAN_DOMAIN, "set_percentage")

    char_target_air_purifier_state_iid = acc.char_target_air_purifier_state.to_HAP()[
        HAP_REPR_IID
    ]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_air_purifier_state_iid,
                    HAP_REPR_VALUE: TARGET_STATE_MANUAL,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_set_percentage[0]
    assert call_set_percentage[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_percentage[0].data[ATTR_PERCENTAGE] == 42
    assert len(events) == 1
    assert events[-1].data["service"] == "set_percentage"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_air_purifier_state_iid,
                    HAP_REPR_VALUE: 1,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_set_preset_mode[0]
    assert call_set_preset_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_preset_mode[0].data[ATTR_PRESET_MODE] == "auto"
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
            ATTR_PRESET_MODES: ["auto"],
        },
    )
    await hass.async_block_till_done()
    assert acc.char_target_air_purifier_state.value == TARGET_STATE_MANUAL