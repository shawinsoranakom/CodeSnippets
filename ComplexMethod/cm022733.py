async def test_windowcovering_cover_set_tilt(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if accessory and HA update slat tilt accordingly."""
    entity_id = "cover.window"

    hass.states.async_set(
        entity_id,
        STATE_UNKNOWN,
        {ATTR_SUPPORTED_FEATURES: CoverEntityFeature.SET_TILT_POSITION},
    )
    await hass.async_block_till_done()
    acc = WindowCovering(hass, hk_driver, "Cover", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 14  # CATEGORY_WINDOW_COVERING

    assert acc.char_current_tilt.value == 0
    assert acc.char_target_tilt.value == 0

    hass.states.async_set(
        entity_id, CoverState.CLOSING, {ATTR_CURRENT_TILT_POSITION: None}
    )
    await hass.async_block_till_done()
    assert acc.char_current_tilt.value == 0
    assert acc.char_target_tilt.value == 0

    hass.states.async_set(
        entity_id, CoverState.CLOSING, {ATTR_CURRENT_TILT_POSITION: 100}
    )
    await hass.async_block_till_done()
    assert acc.char_current_tilt.value == 90
    assert acc.char_target_tilt.value == 90

    hass.states.async_set(
        entity_id, CoverState.CLOSING, {ATTR_CURRENT_TILT_POSITION: 50}
    )
    await hass.async_block_till_done()
    assert acc.char_current_tilt.value == 0
    assert acc.char_target_tilt.value == 0

    hass.states.async_set(
        entity_id, CoverState.CLOSING, {ATTR_CURRENT_TILT_POSITION: 0}
    )
    await hass.async_block_till_done()
    assert acc.char_current_tilt.value == -90
    assert acc.char_target_tilt.value == -90

    # set from HomeKit
    call_set_tilt_position = async_mock_service(
        hass, COVER_DOMAIN, SERVICE_SET_COVER_TILT_POSITION
    )

    # HomeKit sets tilts between -90 and 90 (degrees), whereas
    # Homeassistant expects a % between 0 and 100. Keep that in mind
    # when comparing
    acc.char_target_tilt.client_update_value(90)
    await hass.async_block_till_done()
    assert call_set_tilt_position[0]
    assert call_set_tilt_position[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_tilt_position[0].data[ATTR_TILT_POSITION] == 100
    assert acc.char_current_tilt.value == -90
    assert acc.char_target_tilt.value == 90
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] == 100

    acc.char_target_tilt.client_update_value(45)
    await hass.async_block_till_done()
    assert call_set_tilt_position[1]
    assert call_set_tilt_position[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_set_tilt_position[1].data[ATTR_TILT_POSITION] == 75
    assert acc.char_current_tilt.value == -90
    assert acc.char_target_tilt.value == 45
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] == 75