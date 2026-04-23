async def test_windowcovering_open_close_stop(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA are updated accordingly."""
    entity_id = "cover.window"

    hass.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_SUPPORTED_FEATURES: CoverEntityFeature.STOP}
    )
    acc = WindowCoveringBasic(hass, hk_driver, "Cover", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    # Set from HomeKit
    call_close_cover = async_mock_service(hass, COVER_DOMAIN, "close_cover")
    call_open_cover = async_mock_service(hass, COVER_DOMAIN, "open_cover")
    call_stop_cover = async_mock_service(hass, COVER_DOMAIN, "stop_cover")

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
    assert call_open_cover
    assert call_open_cover[0].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_current_position.value == 100
    assert acc.char_target_position.value == 100
    assert acc.char_position_state.value == 2
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_target_position.client_update_value(55)
    await hass.async_block_till_done()
    assert call_stop_cover
    assert call_stop_cover[0].data[ATTR_ENTITY_ID] == entity_id
    assert acc.char_current_position.value == 50
    assert acc.char_target_position.value == 50
    assert acc.char_position_state.value == 2
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None