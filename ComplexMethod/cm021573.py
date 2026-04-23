async def test_automation_restore_last_triggered_with_initial_state(
    hass: HomeAssistant,
) -> None:
    """Ensure last_triggered is restored, even when initial state is set."""
    time = dt_util.utcnow()

    mock_restore_cache(
        hass,
        (
            State("automation.hello", STATE_ON),
            State("automation.bye", STATE_ON, {"last_triggered": time}),
            State("automation.solong", STATE_OFF, {"last_triggered": time}),
        ),
    )

    config = {
        automation.DOMAIN: [
            {
                "alias": "hello",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"action": "test.automation"},
            },
            {
                "alias": "bye",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"action": "test.automation"},
            },
            {
                "alias": "solong",
                "initial_state": "on",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"action": "test.automation"},
            },
        ]
    }

    await async_setup_component(hass, automation.DOMAIN, config)

    state = hass.states.get("automation.hello")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes["last_triggered"] is None

    state = hass.states.get("automation.bye")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes["last_triggered"] == time

    state = hass.states.get("automation.solong")
    assert state
    assert state.state == STATE_ON
    assert state.attributes["last_triggered"] == time