async def test_timer_restarted_event(hass: HomeAssistant) -> None:
    """Ensure restarted event is called after starting a paused or running timer."""
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

    hass.bus.async_listen(EVENT_TIMER_STARTED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_RESTARTED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_PAUSED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_FINISHED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_CANCELLED, fake_event_listener)

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

    assert results[-1].event_type == EVENT_TIMER_STARTED
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

    assert results[-1].event_type == EVENT_TIMER_RESTARTED
    assert len(results) == 2

    await hass.services.async_call(
        DOMAIN, SERVICE_PAUSE, {CONF_ENTITY_ID: "timer.test1"}
    )
    await hass.async_block_till_done()
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_PAUSED
    assert state.attributes == {
        ATTR_DURATION: "0:00:10",
        ATTR_EDITABLE: False,
        ATTR_REMAINING: "0:00:10",
    }

    assert results[-1].event_type == EVENT_TIMER_PAUSED
    assert len(results) == 3

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

    assert results[-1].event_type == EVENT_TIMER_RESTARTED
    assert len(results) == 4