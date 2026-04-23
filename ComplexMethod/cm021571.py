async def test_automation_restore_state(hass: HomeAssistant) -> None:
    """Ensure states are restored on startup."""
    time = dt_util.utcnow()

    mock_restore_cache(
        hass,
        (
            State("automation.hello", STATE_ON),
            State("automation.bye", STATE_OFF, {"last_triggered": time}),
        ),
    )

    config = {
        automation.DOMAIN: [
            {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event_hello"},
                "action": {"action": "test.automation"},
            },
            {
                "alias": "bye",
                "trigger": {"platform": "event", "event_type": "test_event_bye"},
                "action": {"action": "test.automation"},
            },
        ]
    }

    assert await async_setup_component(hass, automation.DOMAIN, config)

    state = hass.states.get("automation.hello")
    assert state
    assert state.state == STATE_ON
    assert state.attributes["last_triggered"] is None

    state = hass.states.get("automation.bye")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes["last_triggered"] == time

    calls = async_mock_service(hass, "test", "automation")

    assert automation.is_on(hass, "automation.bye") is False

    hass.bus.async_fire("test_event_bye")
    await hass.async_block_till_done()
    assert len(calls) == 0

    assert automation.is_on(hass, "automation.hello")

    hass.bus.async_fire("test_event_hello")
    await hass.async_block_till_done()

    assert len(calls) == 1