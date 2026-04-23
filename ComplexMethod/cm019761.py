async def test_wait_till_timer_expires(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test for a timer to end."""
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 20}}})

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_DURATION: "0:00:20",
        ATTR_EDITABLE: False,
    }

    results = []

    @callback
    def fake_event_listener(event):
        """Fake event listener for trigger."""
        results.append(event)

    hass.bus.async_listen(EVENT_TIMER_STARTED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_PAUSED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_FINISHED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_CANCELLED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_CHANGED, fake_event_listener)

    await hass.services.async_call(
        DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
    )
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_DURATION: "0:00:20",
        ATTR_EDITABLE: False,
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=20)).isoformat(),
        ATTR_REMAINING: "0:00:20",
    }

    assert results[-1].event_type == EVENT_TIMER_STARTED
    assert len(results) == 1

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CHANGE,
        {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: -5},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_DURATION: "0:00:20",
        ATTR_EDITABLE: False,
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=15)).isoformat(),
        ATTR_REMAINING: "0:00:15",
    }

    assert results[-1].event_type == EVENT_TIMER_CHANGED
    assert len(results) == 2

    freezer.tick(10)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_DURATION: "0:00:20",
        ATTR_EDITABLE: False,
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=5)).isoformat(),
        ATTR_REMAINING: "0:00:15",
    }

    freezer.tick(20)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_DURATION: "0:00:20",
        ATTR_EDITABLE: False,
    }

    assert results[-1].event_type == EVENT_TIMER_FINISHED
    assert len(results) == 3