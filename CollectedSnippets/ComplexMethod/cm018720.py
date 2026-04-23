async def test_cancel_all_timers(hass: HomeAssistant, init_components) -> None:
    """Test cancelling all timers."""
    device_id = "test_device"

    started_event = asyncio.Event()
    num_started = 0

    @callback
    def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        nonlocal num_started

        if event_type == TimerEventType.STARTED:
            num_started += 1
            if num_started == 3:
                started_event.set()

    async_register_timer_handler(hass, device_id, handle_timer)

    # Start timers
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
        {"name": {"value": "tv"}, "minutes": {"value": 10}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    result2 = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"name": {"value": "media"}, "minutes": {"value": 15}},
        device_id=device_id,
    )
    assert result2.response_type == intent.IntentResponseType.ACTION_DONE

    # Wait for all timers to start
    async with asyncio.timeout(1):
        await started_event.wait()

    # Cancel all timers
    result = await intent.async_handle(
        hass, "test", intent.INTENT_CANCEL_ALL_TIMERS, {}, device_id=device_id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.speech_slots.get("canceled", 0) == 3

    # No timers should be running for test_device
    result = await intent.async_handle(
        hass, "test", intent.INTENT_TIMER_STATUS, {}, device_id=device_id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 0