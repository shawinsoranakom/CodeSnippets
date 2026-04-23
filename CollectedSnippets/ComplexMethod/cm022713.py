async def test_fan_auto_manual(
    hass: HomeAssistant,
    hk_driver,
    events: list[Event],
    auto_preset: str,
    preset_modes: list[str],
) -> None:
    """Test switching between Auto and Manual."""
    entity_id = "fan.demo"

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED,
            ATTR_PRESET_MODE: auto_preset,
            ATTR_PRESET_MODES: preset_modes,
        },
    )
    await hass.async_block_till_done()
    acc = AirPurifier(hass, hk_driver, "Air Purifier", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.preset_mode_chars["smart"].value == 0
    assert acc.preset_mode_chars["sleep"].value == 0
    assert acc.auto_preset is not None

    # Auto presets are handled as the target air purifier state, so
    # not supposed to be exposed as a separate switch
    switches = set()
    for service in acc.services:
        if service.display_name == "Switch":
            switches.add(service.unique_id)

    assert len(switches) == len(preset_modes) - 1
    for preset in preset_modes:
        if preset != auto_preset:
            assert preset in switches
        else:
            # Auto preset should not be in switches
            assert preset not in switches

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_target_air_purifier_state.value == TARGET_STATE_AUTO

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED,
            ATTR_PRESET_MODE: "smart",
            ATTR_PRESET_MODES: preset_modes,
        },
    )
    await hass.async_block_till_done()

    assert acc.preset_mode_chars["smart"].value == 1
    assert acc.char_target_air_purifier_state.value == TARGET_STATE_MANUAL

    # Set from HomeKit
    call_set_preset_mode = async_mock_service(hass, FAN_DOMAIN, "set_preset_mode")
    call_set_percentage = async_mock_service(hass, FAN_DOMAIN, "set_percentage")
    char_auto_iid = acc.char_target_air_purifier_state.to_HAP()[HAP_REPR_IID]

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

    assert acc.char_target_air_purifier_state.value == TARGET_STATE_AUTO
    assert len(call_set_preset_mode) == 1
    assert call_set_preset_mode[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_preset_mode[0].data[ATTR_PRESET_MODE] == auto_preset
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
    assert acc.char_target_air_purifier_state.value == TARGET_STATE_MANUAL
    assert len(call_set_percentage) == 1
    assert call_set_percentage[0].data[ATTR_ENTITY_ID] == entity_id
    assert events[-1].data["service"] == "set_percentage"
    assert len(events) == 2