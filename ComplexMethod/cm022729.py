async def test_garage_door_open_close(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "cover.garage_door"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = GarageDoorOpener(hass, hk_driver, "Garage Door", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 4  # GarageDoorOpener

    assert acc.char_current_state.value == HK_DOOR_OPEN
    assert acc.char_target_state.value == HK_DOOR_OPEN

    hass.states.async_set(
        entity_id, CoverState.CLOSED, {ATTR_OBSTRUCTION_DETECTED: False}
    )
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_CLOSED
    assert acc.char_target_state.value == HK_DOOR_CLOSED
    assert acc.char_obstruction_detected.value is False

    hass.states.async_set(entity_id, CoverState.OPEN, {ATTR_OBSTRUCTION_DETECTED: True})
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_OPEN
    assert acc.char_target_state.value == HK_DOOR_OPEN
    assert acc.char_obstruction_detected.value is True

    hass.states.async_set(
        entity_id, STATE_UNAVAILABLE, {ATTR_OBSTRUCTION_DETECTED: True}
    )
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_OPEN
    assert acc.char_target_state.value == HK_DOOR_OPEN
    assert acc.char_obstruction_detected.value is True
    assert acc.available is False

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_OPEN
    assert acc.char_target_state.value == HK_DOOR_OPEN
    assert acc.available is True

    # Set from HomeKit
    call_close_cover = async_mock_service(hass, COVER_DOMAIN, "close_cover")
    call_open_cover = async_mock_service(hass, COVER_DOMAIN, "open_cover")

    acc.char_target_state.client_update_value(1)
    await hass.async_block_till_done()
    assert call_close_cover
    assert call_close_cover[0].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_current_state.value == HK_DOOR_CLOSING
    assert acc.char_target_state.value == HK_DOOR_CLOSED
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    hass.states.async_set(entity_id, CoverState.CLOSED)
    await hass.async_block_till_done()

    acc.char_target_state.client_update_value(1)
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_CLOSED
    assert acc.char_target_state.value == HK_DOOR_CLOSED
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_target_state.client_update_value(0)
    await hass.async_block_till_done()
    assert call_open_cover
    assert call_open_cover[0].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_current_state.value == HK_DOOR_OPENING
    assert acc.char_target_state.value == HK_DOOR_OPEN
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None

    hass.states.async_set(entity_id, CoverState.OPEN)
    await hass.async_block_till_done()

    acc.char_target_state.client_update_value(0)
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_OPEN
    assert acc.char_target_state.value == HK_DOOR_OPEN
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None