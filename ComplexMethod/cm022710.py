async def test_fan_multiple_preset_modes(
    hass: HomeAssistant, hk_driver: HomeDriver, events: list[Event]
) -> None:
    """Test fan with multiple preset modes."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE,
            ATTR_PRESET_MODE: "auto",
            ATTR_PRESET_MODES: ["auto", "smart"],
        },
    )
    await hass.async_block_till_done()
    acc = Fan(hass, hk_driver, "Fan", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.preset_mode_chars["auto"].value == 1
    assert acc.preset_mode_chars["smart"].value == 0
    switch_service = acc.get_service(SERV_SWITCH)
    configured_name_char = switch_service.get_characteristic(CHAR_CONFIGURED_NAME)
    assert configured_name_char.value == "auto"

    acc.run()
    await hass.async_block_till_done()

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE,
            ATTR_PRESET_MODE: "smart",
            ATTR_PRESET_MODES: ["auto", "smart"],
        },
    )
    await hass.async_block_till_done()

    assert acc.preset_mode_chars["auto"].value == 0
    assert acc.preset_mode_chars["smart"].value == 1
    # Set from HomeKit
    call_set_preset_mode = async_mock_service(hass, FAN_DOMAIN, "set_preset_mode")
    call_turn_on = async_mock_service(hass, FAN_DOMAIN, "turn_on")

    char_auto_iid = acc.preset_mode_chars["auto"].to_HAP()[HAP_REPR_IID]

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_auto_iid,
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
    assert len(events) == 1
    assert events[-1].data["service"] == "set_preset_mode"

    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_auto_iid,
                    HAP_REPR_VALUE: 0,
                },
            ]
        },
        "mock_addr",
    )
    await hass.async_block_till_done()
    assert call_turn_on[0]
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert events[-1].data["service"] == "turn_on"
    assert len(events) == 2