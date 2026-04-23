async def test_statemachine_report_state(hass: HomeAssistant) -> None:
    """Test report state event."""

    @ha.callback
    def mock_filter(event_data):
        """Mock filter."""
        return True

    @callback
    def listener(event: ha.Event) -> None:
        state_reported_events.append(event)

    hass.states.async_set("light.bowl", "on", {})
    state_changed_events = async_capture_events(hass, EVENT_STATE_CHANGED)
    state_reported_events = []
    unsub = hass.bus.async_listen(
        EVENT_STATE_REPORTED, listener, event_filter=mock_filter
    )

    hass.states.async_set("light.bowl", "on")
    await hass.async_block_till_done()
    assert len(state_changed_events) == 0
    assert len(state_reported_events) == 1

    hass.states.async_set("light.bowl", "on", None, True)
    await hass.async_block_till_done()
    assert len(state_changed_events) == 1
    assert len(state_reported_events) == 1

    hass.states.async_set("light.bowl", "off")
    await hass.async_block_till_done()
    assert len(state_changed_events) == 2
    assert len(state_reported_events) == 1

    hass.states.async_remove("light.bowl")
    await hass.async_block_till_done()
    assert len(state_changed_events) == 3
    assert len(state_reported_events) == 1

    unsub()

    hass.states.async_set("light.bowl", "on")
    await hass.async_block_till_done()
    assert len(state_changed_events) == 4
    assert len(state_reported_events) == 1