async def test_shared_context(hass: HomeAssistant) -> None:
    """Test that the shared context is passed down the chain."""
    event = "test_event"
    context = Context()

    event_mock = Mock()
    run_mock = Mock()

    hass.bus.async_listen(event, event_mock)
    hass.bus.async_listen(EVENT_SCRIPT_STARTED, run_mock)

    assert await async_setup_component(
        hass, "script", {"script": {"test": {"sequence": [{"event": event}]}}}
    )

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID}, context=context
    )
    await hass.async_block_till_done()

    assert event_mock.call_count == 1
    assert run_mock.call_count == 1

    args, _kwargs = run_mock.call_args
    assert args[0].context == context
    # Ensure event data has all attributes set
    assert args[0].data.get(ATTR_NAME) == "test"
    assert args[0].data.get(ATTR_ENTITY_ID) == "script.test"

    # Ensure context carries through the event
    args, _kwargs = event_mock.call_args
    assert args[0].context == context

    # Ensure the script state shares the same context
    state = hass.states.get("script.test")
    assert state is not None
    assert state.context == context