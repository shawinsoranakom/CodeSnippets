async def test_pause_unpause_timer_disambiguate(
    hass: HomeAssistant, init_components
) -> None:
    """Test disamgibuating timers by their paused state."""
    device_id = "test_device"
    started_timer_ids: list[str] = []
    paused_timer_ids: list[str] = []
    unpaused_timer_ids: list[str] = []

    started_event = asyncio.Event()
    updated_event = asyncio.Event()

    @callback
    def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        if event_type == TimerEventType.STARTED:
            started_event.set()
            started_timer_ids.append(timer.id)
        elif event_type == TimerEventType.UPDATED:
            updated_event.set()
            if timer.is_active:
                unpaused_timer_ids.append(timer.id)
            else:
                paused_timer_ids.append(timer.id)

    async_register_timer_handler(hass, device_id, handle_timer)

    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"minutes": {"value": 5}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await started_event.wait()

    # Pause the timer
    result = await intent.async_handle(
        hass, "test", intent.INTENT_PAUSE_TIMER, {}, device_id=device_id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await updated_event.wait()

    # Start another timer
    started_event.clear()
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"minutes": {"value": 10}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await started_event.wait()
        assert len(started_timer_ids) == 2

    # We can pause the more recent timer without more information because the
    # first one is paused.
    updated_event.clear()
    result = await intent.async_handle(
        hass, "test", intent.INTENT_PAUSE_TIMER, {}, device_id=device_id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await updated_event.wait()
        assert len(paused_timer_ids) == 2
        assert paused_timer_ids[1] == started_timer_ids[1]

    # We have to explicitly unpause now
    updated_event.clear()
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_UNPAUSE_TIMER,
        {"start_minutes": {"value": 10}},
        device_id=device_id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await updated_event.wait()
        assert len(unpaused_timer_ids) == 1
        assert unpaused_timer_ids[0] == started_timer_ids[1]

    # We can resume the older timer without more information because the
    # second one is running.
    updated_event.clear()
    result = await intent.async_handle(
        hass, "test", intent.INTENT_UNPAUSE_TIMER, {}, device_id=device_id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await updated_event.wait()
        assert len(unpaused_timer_ids) == 2
        assert unpaused_timer_ids[1] == started_timer_ids[0]