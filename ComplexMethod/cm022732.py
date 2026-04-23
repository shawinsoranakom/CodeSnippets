async def test_window_instantiate_set_position(hass: HomeAssistant, hk_driver) -> None:
    """Test if Window accessory is instantiated correctly and can set position."""
    entity_id = "cover.window"

    hass.states.async_set(
        entity_id,
        CoverState.OPEN,
        {
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
            ATTR_CURRENT_POSITION: 0,
        },
    )
    await hass.async_block_till_done()
    acc = Window(hass, hk_driver, "Window", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 13  # Window

    assert acc.char_current_position.value == 0
    assert acc.char_target_position.value == 0

    hass.states.async_set(
        entity_id,
        CoverState.OPEN,
        {
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
            ATTR_CURRENT_POSITION: 50,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 50
    assert acc.char_target_position.value == 50
    assert acc.char_position_state.value == 2

    hass.states.async_set(
        entity_id,
        CoverState.OPEN,
        {
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
            ATTR_CURRENT_POSITION: "GARBAGE",
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 50
    assert acc.char_target_position.value == 50
    assert acc.char_position_state.value == 2