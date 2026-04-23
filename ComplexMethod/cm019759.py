async def test_methods_and_events(hass: HomeAssistant) -> None:
    """Test methods and events."""
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}})

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_DURATION: "0:00:10",
        ATTR_EDITABLE: False,
    }

    results: list[tuple[Event, State | None]] = []

    @callback
    def fake_event_listener(event: Event):
        """Fake event listener for trigger."""
        results.append((event, hass.states.get("timer.test1")))

    hass.bus.async_listen(EVENT_TIMER_STARTED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_RESTARTED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_PAUSED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_FINISHED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_CANCELLED, fake_event_listener)
    hass.bus.async_listen(EVENT_TIMER_CHANGED, fake_event_listener)

    finish_10 = (utcnow() + timedelta(seconds=10)).isoformat()
    finish_5 = (utcnow() + timedelta(seconds=5)).isoformat()

    steps = [
        {
            "call": SERVICE_START,
            "call_data": {},
            "expected_state": STATUS_ACTIVE,
            "expected_extra_attributes": {
                ATTR_FINISHES_AT: finish_10,
                ATTR_REMAINING: "0:00:10",
            },
            "expected_event": EVENT_TIMER_STARTED,
        },
        {
            "call": SERVICE_PAUSE,
            "call_data": {},
            "expected_state": STATUS_PAUSED,
            "expected_extra_attributes": {ATTR_REMAINING: "0:00:10"},
            "expected_event": EVENT_TIMER_PAUSED,
        },
        {
            "call": SERVICE_START,
            "call_data": {},
            "expected_state": STATUS_ACTIVE,
            "expected_extra_attributes": {
                ATTR_FINISHES_AT: finish_10,
                ATTR_REMAINING: "0:00:10",
            },
            "expected_event": EVENT_TIMER_RESTARTED,
        },
        {
            "call": SERVICE_CANCEL,
            "call_data": {},
            "expected_state": STATUS_IDLE,
            "expected_extra_attributes": {},
            "expected_event": EVENT_TIMER_CANCELLED,
        },
        {
            "call": SERVICE_CANCEL,
            "call_data": {},
            "expected_state": STATUS_IDLE,
            "expected_extra_attributes": {},
            "expected_event": None,
        },
        {
            "call": SERVICE_START,
            "call_data": {},
            "expected_state": STATUS_ACTIVE,
            "expected_extra_attributes": {
                ATTR_FINISHES_AT: finish_10,
                ATTR_REMAINING: "0:00:10",
            },
            "expected_event": EVENT_TIMER_STARTED,
        },
        {
            "call": SERVICE_FINISH,
            "call_data": {},
            "expected_state": STATUS_IDLE,
            "expected_extra_attributes": {},
            "expected_event": EVENT_TIMER_FINISHED,
        },
        {
            "call": SERVICE_FINISH,
            "call_data": {},
            "expected_state": STATUS_IDLE,
            "expected_extra_attributes": {},
            "expected_event": None,
        },
        {
            "call": SERVICE_START,
            "call_data": {},
            "expected_state": STATUS_ACTIVE,
            "expected_extra_attributes": {
                ATTR_FINISHES_AT: finish_10,
                ATTR_REMAINING: "0:00:10",
            },
            "expected_event": EVENT_TIMER_STARTED,
        },
        {
            "call": SERVICE_PAUSE,
            "call_data": {},
            "expected_state": STATUS_PAUSED,
            "expected_extra_attributes": {ATTR_REMAINING: "0:00:10"},
            "expected_event": EVENT_TIMER_PAUSED,
        },
        {
            "call": SERVICE_CANCEL,
            "call_data": {},
            "expected_state": STATUS_IDLE,
            "expected_extra_attributes": {},
            "expected_event": EVENT_TIMER_CANCELLED,
        },
        {
            "call": SERVICE_START,
            "call_data": {},
            "expected_state": STATUS_ACTIVE,
            "expected_extra_attributes": {
                ATTR_FINISHES_AT: finish_10,
                ATTR_REMAINING: "0:00:10",
            },
            "expected_event": EVENT_TIMER_STARTED,
        },
        {
            "call": SERVICE_CHANGE,
            "call_data": {CONF_DURATION: -5},
            "expected_state": STATUS_ACTIVE,
            "expected_extra_attributes": {
                ATTR_FINISHES_AT: finish_5,
                ATTR_REMAINING: "0:00:05",
            },
            "expected_event": EVENT_TIMER_CHANGED,
        },
        {
            "call": SERVICE_START,
            "call_data": {},
            "expected_state": STATUS_ACTIVE,
            "expected_extra_attributes": {
                ATTR_FINISHES_AT: finish_5,
                ATTR_REMAINING: "0:00:05",
            },
            "expected_event": EVENT_TIMER_RESTARTED,
        },
        {
            "call": SERVICE_PAUSE,
            "call_data": {},
            "expected_state": STATUS_PAUSED,
            "expected_extra_attributes": {ATTR_REMAINING: "0:00:05"},
            "expected_event": EVENT_TIMER_PAUSED,
        },
        {
            "call": SERVICE_FINISH,
            "call_data": {},
            "expected_state": STATUS_IDLE,
            "expected_extra_attributes": {},
            "expected_event": EVENT_TIMER_FINISHED,
        },
    ]

    expected_events = 0
    for step in steps:
        if step["call"] is not None:
            await hass.services.async_call(
                DOMAIN,
                step["call"],
                {CONF_ENTITY_ID: "timer.test1", **step["call_data"]},
                blocking=True,
            )
            await hass.async_block_till_done()

        state = hass.states.get("timer.test1")
        assert state
        if step["expected_state"] is not None:
            assert state.state == step["expected_state"]
            assert (
                state.attributes
                == {
                    ATTR_DURATION: "0:00:10",
                    ATTR_EDITABLE: False,
                }
                | step["expected_extra_attributes"]
            )

        if step["expected_event"] is not None:
            expected_events += 1
            last_result = results[-1]
            event, state = last_result
            assert event.event_type == step["expected_event"]
            assert state.state == step["expected_state"]
            assert (
                state.attributes
                == {
                    ATTR_DURATION: "0:00:10",
                    ATTR_EDITABLE: False,
                }
                | step["expected_extra_attributes"]
            )
            assert len(results) == expected_events