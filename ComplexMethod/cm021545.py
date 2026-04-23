async def test_template_state_text_with_position(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the state of a position template in order."""
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == STATE_UNKNOWN

    # Test the open/closed states are ignored when state template updates.
    await async_trigger(hass, TEST_STATE_ENTITY_ID, CoverState.OPEN)
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == STATE_UNKNOWN

    await async_trigger(hass, TEST_STATE_ENTITY_ID, CoverState.CLOSED)
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == STATE_UNKNOWN

    # Test the opening/closing state are honored when state template updates.
    await async_trigger(hass, TEST_STATE_ENTITY_ID, CoverState.OPENING)
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == CoverState.OPENING

    await async_trigger(hass, TEST_STATE_ENTITY_ID, CoverState.CLOSING)
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == CoverState.CLOSING

    # Test the open/closed states are honored when position template updates.
    await async_trigger(hass, TEST_POSITION_ENTITY_ID, 0)
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == CoverState.CLOSING
    assert state.attributes.get("current_position") == 0

    # Test the closed state is ignored when position is already set.
    await async_trigger(hass, TEST_STATE_ENTITY_ID, CoverState.OPEN)
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == CoverState.CLOSED
    assert state.attributes.get("current_position") == 0

    # Test the open/closed states are honored when position template updates.
    await async_trigger(hass, TEST_POSITION_ENTITY_ID, 10)
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == CoverState.OPEN
    assert state.attributes.get("current_position") == 10

    assert "Received invalid cover state" not in caplog.text

    await async_trigger(hass, TEST_STATE_ENTITY_ID, "dog")
    state = hass.states.get(TEST_COVER.entity_id)
    assert state.state == CoverState.OPEN
    assert state.attributes.get("current_position") == 10
    assert "Received invalid cover state: dog" in caplog.text