async def test_state_change_events_match_time_with_limits_of_precision(
    hass: HomeAssistant,
) -> None:
    """Ensure last_updated matches last_updated_timestamp within limits of precision.

    The last_updated_timestamp uses the same precision as time.time() which is
    a bit better than the precision of datetime.now() which is used for last_updated
    on some platforms.
    """
    events = async_capture_events(hass, EVENT_STATE_CHANGED)
    hass.states.async_set("light.bedroom", "on")
    await hass.async_block_till_done()
    state: State = hass.states.get("light.bedroom")
    assert state.last_updated == events[0].time_fired
    assert state.last_updated_timestamp == pytest.approx(
        events[0].time_fired.timestamp()
    )
    assert state.last_updated_timestamp == pytest.approx(state.last_updated.timestamp())
    assert state.last_updated_timestamp == state.last_changed_timestamp
    assert state.last_updated_timestamp == pytest.approx(state.last_changed.timestamp())
    assert state.last_updated_timestamp == state.last_reported_timestamp
    assert state.last_updated_timestamp == pytest.approx(
        state.last_reported.timestamp()
    )