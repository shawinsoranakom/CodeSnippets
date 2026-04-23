async def test_trigger_action_variables(hass: HomeAssistant) -> None:
    """Test trigger entity with variables in an action works."""
    event = "test_event2"
    context = Context()
    events = async_capture_events(hass, event)

    state = hass.states.get("sensor.hello_name")
    assert state is not None
    assert state.state == STATE_UNKNOWN

    context = Context()
    hass.bus.async_fire("test_event", {"a": 1}, context=context)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.hello_name")
    assert state.state == str(1 + 2 + 3)
    assert state.context is context
    assert state.attributes["a"] == 1
    assert state.attributes["b"] == 2
    assert state.attributes["c"] == 3

    assert len(events) == 1
    assert events[0].context.parent_id == context.id