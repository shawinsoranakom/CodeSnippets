async def test_opening(hass: HomeAssistant) -> None:
    """Test the opening of a valve."""
    state = hass.states.get(ORCHARD)
    assert state is not None
    assert state.state == ValveState.CLOSED
    await hass.async_block_till_done()

    state_changes = async_capture_events(hass, EVENT_STATE_CHANGED)
    await hass.services.async_call(
        VALVE_DOMAIN, SERVICE_OPEN_VALVE, {ATTR_ENTITY_ID: ORCHARD}, blocking=False
    )
    await hass.async_block_till_done()

    assert state_changes[0].data["entity_id"] == ORCHARD
    assert state_changes[0].data["new_state"] is not None
    assert state_changes[0].data["new_state"].state == ValveState.OPENING

    assert state_changes[1].data["entity_id"] == ORCHARD
    assert state_changes[1].data["new_state"] is not None
    assert state_changes[1].data["new_state"].state == ValveState.OPEN