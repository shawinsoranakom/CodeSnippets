async def test_dual_roller_shutter_position_tests(
    hass: HomeAssistant, mock_dual_roller_shutter: AsyncMock
) -> None:
    """Validate current_position and open/closed state."""

    entity_id_dual = "cover.test_dual_roller_shutter"
    entity_id_lower = "cover.test_dual_roller_shutter_lower_shutter"
    entity_id_upper = "cover.test_dual_roller_shutter_upper_shutter"

    # device position is inverted (100 - x)
    mock_dual_roller_shutter.position.position_percent = 29
    mock_dual_roller_shutter.position_upper_curtain.position_percent = 28
    mock_dual_roller_shutter.position_lower_curtain.position_percent = 27
    await update_callback_entity(hass, mock_dual_roller_shutter)
    state = hass.states.get(entity_id_dual)
    assert state is not None
    assert state.attributes.get("current_position") == 71
    assert state.state == STATE_OPEN

    state = hass.states.get(entity_id_upper)
    assert state is not None
    assert state.attributes.get("current_position") == 72
    assert state.state == STATE_OPEN

    state = hass.states.get(entity_id_lower)
    assert state is not None
    assert state.attributes.get("current_position") == 73
    assert state.state == STATE_OPEN

    mock_dual_roller_shutter.position.closed = True
    mock_dual_roller_shutter.position_upper_curtain.closed = True
    mock_dual_roller_shutter.position_lower_curtain.closed = True
    await update_callback_entity(hass, mock_dual_roller_shutter)
    state = hass.states.get(entity_id_dual)
    assert state is not None
    assert state.state == STATE_CLOSED

    state = hass.states.get(entity_id_upper)
    assert state is not None
    assert state.state == STATE_CLOSED

    state = hass.states.get(entity_id_lower)
    assert state is not None
    assert state.state == STATE_CLOSED