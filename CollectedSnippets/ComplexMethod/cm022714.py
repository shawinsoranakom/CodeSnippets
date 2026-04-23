async def test_presets_no_auto(
    hass: HomeAssistant,
    hk_driver,
    events: list[Event],
) -> None:
    """Test preset without an auto mode."""
    entity_id = "fan.demo"

    preset_modes = ["sleep", "smart"]
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
    acc = AirPurifier(hass, hk_driver, "Air Purifier", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    assert acc.preset_mode_chars["smart"].value == 1
    assert acc.preset_mode_chars["sleep"].value == 0
    assert acc.auto_preset is None

    # Auto presets are handled as the target air purifier state, so
    # not supposed to be exposed as a separate switch
    switches = set()
    for service in acc.services:
        if service.display_name == "Switch":
            switches.add(service.unique_id)

    assert len(switches) == len(preset_modes)
    for preset in preset_modes:
        assert preset in switches

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_target_air_purifier_state.value == TARGET_STATE_MANUAL

    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.PRESET_MODE
            | FanEntityFeature.SET_SPEED,
            ATTR_PRESET_MODE: "sleep",
            ATTR_PRESET_MODES: preset_modes,
        },
    )
    await hass.async_block_till_done()

    assert acc.preset_mode_chars["smart"].value == 0
    assert acc.preset_mode_chars["sleep"].value == 1
    assert acc.char_target_air_purifier_state.value == TARGET_STATE_MANUAL