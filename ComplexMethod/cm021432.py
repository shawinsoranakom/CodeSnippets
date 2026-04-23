async def test_closing(hass: HomeAssistant) -> None:
    """Test the closing of a valve."""
    state = hass.states.get(FRONT_GARDEN)
    assert state is not None
    assert state.state == ValveState.OPEN
    await hass.async_block_till_done()

    state_changes = async_capture_events(hass, EVENT_STATE_CHANGED)
    await hass.services.async_call(
        VALVE_DOMAIN,
        SERVICE_CLOSE_VALVE,
        {ATTR_ENTITY_ID: FRONT_GARDEN},
        blocking=False,
    )
    await hass.async_block_till_done()

    assert state_changes[0].data["entity_id"] == FRONT_GARDEN
    assert state_changes[0].data["new_state"] is not None
    assert state_changes[0].data["new_state"].state == ValveState.CLOSING

    assert state_changes[1].data["entity_id"] == FRONT_GARDEN
    assert state_changes[1].data["new_state"] is not None
    assert state_changes[1].data["new_state"].state == ValveState.CLOSED