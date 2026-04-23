async def test_timer_status_with_names(hass: HomeAssistant, init_components) -> None:
    """Test getting the status of named timers."""
    device_id = "test_device"

    started_event = asyncio.Event()
    num_started = 0

    @callback
    def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        nonlocal num_started

        if event_type == TimerEventType.STARTED:
            num_started += 1
            if num_started == 4:
                started_event.set()

    async_register_timer_handler(hass, device_id, handle_timer)

    # Start timers with names
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"name": {"value": "pizza"}, "minutes": {"value": 10}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"name": {"value": "pizza"}, "minutes": {"value": 15}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"name": {"value": "cookies"}, "minutes": {"value": 20}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"name": {"value": "chicken"}, "hours": {"value": 2}, "seconds": {"value": 30}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Wait for all timers to start
    async with asyncio.timeout(1):
        await started_event.wait()

    # No constraints returns all timers
    for handle_device_id in (device_id, None):
        result = await intent.async_handle(
            hass, "test", intent.INTENT_TIMER_STATUS, {}, device_id=handle_device_id
        )
        assert result.response_type == intent.IntentResponseType.ACTION_DONE
        timers = result.speech_slots.get("timers", [])
        assert len(timers) == 4
        assert {t.get(ATTR_NAME) for t in timers} == {"pizza", "cookies", "chicken"}

    # Get status of cookie timer
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_TIMER_STATUS,
        {"name": {"value": "cookies"}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 1
    assert timers[0].get(ATTR_NAME) == "cookies"
    assert timers[0].get("start_minutes") == 20

    # Get status of pizza timers
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_TIMER_STATUS,
        {"name": {"value": "pizza"}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 2
    assert timers[0].get(ATTR_NAME) == "pizza"
    assert timers[1].get(ATTR_NAME) == "pizza"
    assert {timers[0].get("start_minutes"), timers[1].get("start_minutes")} == {10, 15}

    # Get status of one pizza timer
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_TIMER_STATUS,
        {"name": {"value": "pizza"}, "start_minutes": {"value": 10}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 1
    assert timers[0].get(ATTR_NAME) == "pizza"
    assert timers[0].get("start_minutes") == 10

    # Get status of one chicken timer
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_TIMER_STATUS,
        {
            "name": {"value": "chicken"},
            "start_hours": {"value": 2},
            "start_seconds": {"value": 30},
        },
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 1
    assert timers[0].get(ATTR_NAME) == "chicken"
    assert timers[0].get("start_hours") == 2
    assert timers[0].get("start_minutes") == 0
    assert timers[0].get("start_seconds") == 30

    # Wrong name results in an empty list
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_TIMER_STATUS,
        {"name": {"value": "does-not-exist"}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 0

    # Wrong start time results in an empty list
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_TIMER_STATUS,
        {
            "start_hours": {"value": 100},
            "start_minutes": {"value": 100},
            "start_seconds": {"value": 100},
        },
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 0