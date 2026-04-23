async def test_windowcovering_open_close(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "cover.window"

    hass.states.async_set(entity_id, STATE_UNKNOWN, {ATTR_SUPPORTED_FEATURES: 0})
    acc = WindowCoveringBasic(hass, hk_driver, "Cover", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 14  # WindowCovering

    assert acc.char_current_position.value == 0
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 2

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 0
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 2

    hass.states.async_set(entity_id, CoverState.OPENING)
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 0
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 1

    hass.states.async_set(entity_id, CoverState.OPEN)
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 100
    assert acc.char_target_position.value == 100
    assert acc.char_position_state.value == 2

    hass.states.async_set(entity_id, CoverState.CLOSING)
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 100
    assert acc.char_target_position.value == 100
    assert acc.char_position_state.value == 0

    hass.states.async_set(entity_id, CoverState.CLOSED)
    await hass.async_block_till_done()
    assert acc.char_current_position.value == 0
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 2

    # Set from HomeKit
    call_close_cover = async_mock_service(hass, COVER_DOMAIN, "close_cover")
    call_open_cover = async_mock_service(hass, COVER_DOMAIN, "open_cover")

    acc.char_target_position.client_update_value(25)
    await hass.async_block_till_done()
    assert call_close_cover
    assert call_close_cover[0].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_current_position.value == 0
    assert acc.char_target_position.value == 0
    assert acc.char_position_state.value == 2
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_target_position.client_update_value(90)
    await hass.async_block_till_done()
    assert call_open_cover[0]
    assert call_open_cover[0].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_current_position.value == 100
    assert acc.char_target_position.value == 100
    assert acc.char_position_state.value == 2
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_target_position.client_update_value(55)
    await hass.async_block_till_done()
    assert call_open_cover[1]
    assert call_open_cover[1].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_current_position.value == 100
    assert acc.char_target_position.value == 100
    assert acc.char_position_state.value == 2
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None