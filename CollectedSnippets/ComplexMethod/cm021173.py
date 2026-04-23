async def test_window_current_position_and_opening_closing_states(
    hass: HomeAssistant, mock_window: AsyncMock
) -> None:
    """Validate current_position and opening/closing state transitions."""

    entity_id = "cover.test_window"

    # device position 30 -> current_position 70
    mock_window.position.position_percent = 30
    await update_callback_entity(hass, mock_window)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes.get("current_position") == 70
    assert state.state == STATE_OPEN

    # Opening
    mock_window.is_opening = True
    mock_window.is_closing = False
    await update_callback_entity(hass, mock_window)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OPENING

    # Closing
    mock_window.is_opening = False
    mock_window.is_closing = True
    await update_callback_entity(hass, mock_window)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_CLOSING