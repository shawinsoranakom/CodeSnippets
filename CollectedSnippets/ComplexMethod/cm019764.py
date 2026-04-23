async def test_state_changed_when_timer_restarted(hass: HomeAssistant) -> None:
    """Ensure timer's state changes when it restarted."""
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}})

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_DURATION: "0:00:10",
        ATTR_EDITABLE: False,
    }

    results = []

    @callback
    def fake_event_listener(event):
        """Fake event listener for trigger."""
        results.append(event)

    hass.bus.async_listen(EVENT_STATE_CHANGED, fake_event_listener)

    await hass.services.async_call(
        DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}
    )
    await hass.async_block_till_done()
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_DURATION: "0:00:10",
        ATTR_EDITABLE: False,
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
        ATTR_REMAINING: "0:00:10",
    }

    assert results[-1].event_type == EVENT_STATE_CHANGED
    assert len(results) == 1

    await hass.services.async_call(
        DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}
    )
    await hass.async_block_till_done()
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_DURATION: "0:00:10",
        ATTR_EDITABLE: False,
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
        ATTR_REMAINING: "0:00:10",
    }

    assert results[-1].event_type == EVENT_STATE_CHANGED
    assert len(results) == 2