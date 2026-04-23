async def test_shared_context(hass: HomeAssistant, calls: list[ServiceCall]) -> None:
    """Test that the shared context is passed down the chain."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {"event": "test_event2"},
                },
                {
                    "alias": "bye",
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "action": {"action": "test.automation"},
                },
            ]
        },
    )

    context = Context()
    first_automation_listener = Mock()
    event_mock = Mock()

    hass.bus.async_listen("test_event2", first_automation_listener)
    hass.bus.async_listen(EVENT_AUTOMATION_TRIGGERED, event_mock)
    hass.bus.async_fire("test_event", context=context)
    await hass.async_block_till_done()

    # Ensure events was fired
    assert first_automation_listener.call_count == 1
    assert event_mock.call_count == 2

    # Verify automation triggered evenet for 'hello' automation
    args, _ = event_mock.call_args_list[0]
    first_trigger_context = args[0].context
    assert first_trigger_context.parent_id == context.id
    # Ensure event data has all attributes set
    assert args[0].data.get(ATTR_NAME) is not None
    assert args[0].data.get(ATTR_ENTITY_ID) is not None
    assert args[0].data.get(ATTR_SOURCE) is not None

    # Ensure context set correctly for event fired by 'hello' automation
    args, _ = first_automation_listener.call_args
    assert args[0].context is first_trigger_context

    # Ensure the 'hello' automation state has the right context
    state = hass.states.get("automation.hello")
    assert state is not None
    assert state.context is first_trigger_context

    # Verify automation triggered evenet for 'bye' automation
    args, _ = event_mock.call_args_list[1]
    second_trigger_context = args[0].context
    assert second_trigger_context.parent_id == first_trigger_context.id
    # Ensure event data has all attributes set
    assert args[0].data.get(ATTR_NAME) is not None
    assert args[0].data.get(ATTR_ENTITY_ID) is not None
    assert args[0].data.get(ATTR_SOURCE) is not None

    # Ensure the service call from the second automation
    # shares the same context
    assert len(calls) == 1
    assert calls[0].context is second_trigger_context