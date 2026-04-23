async def test_windowcovering_set_cover_position(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "cover.window"

    hass.states.async_set(
        entity_id,
        STATE_UNKNOWN,
        {ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION},
    )
    await hass.async_block_till_done()
    acc = WindowCovering(hass, hk_driver, "Cover", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 14  # WindowCovering

    assert acc.char_current_position.value == 0
    assert acc.char_target_position.value == 0

    hass.states.async_set(
        entity_id,
        STATE_UNKNOWN,
        {
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
            ATTR_CURRENT_POSITION: None,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 0
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 2

    hass.states.async_set(
        entity_id,
        CoverState.OPENING,
        {
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
            ATTR_CURRENT_POSITION: 60,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 60
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 1

    hass.states.async_set(
        entity_id,
        CoverState.OPENING,
        {
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
            ATTR_CURRENT_POSITION: 70.0,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 70
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 1

    hass.states.async_set(
        entity_id,
        CoverState.CLOSING,
        {
            ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_POSITION,
            ATTR_CURRENT_POSITION: 50,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 50
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 0

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

    # Set from HomeKit
    call_set_cover_position = async_mock_service(
        hass, COVER_DOMAIN, "set_cover_position"
    )

    acc.char_target_position.client_update_value(25)
    await hass.async_block_till_done()
    assert call_set_cover_position[0]
    assert call_set_cover_position[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_cover_position[0].data[ATTR_POSITION] == 25
    assert acc.char_current_position.value == 50
    assert acc.char_target_position.value == 25
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == 25

    acc.char_target_position.client_update_value(75)
    await hass.async_block_till_done()
    assert call_set_cover_position[1]
    assert call_set_cover_position[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_cover_position[1].data[ATTR_POSITION] == 75
    assert acc.char_current_position.value == 50
    assert acc.char_target_position.value == 75
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == 75