async def test_cancel_all_timers_area(
    hass: HomeAssistant,
    init_components,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test cancelling all timers in an area."""
    entry = MockConfigEntry()
    entry.add_to_hass(hass)

    area_kitchen = area_registry.async_create("kitchen")
    device_kitchen = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("test", "kitchen-device")},
    )
    device_registry.async_update_device(device_kitchen.id, area_id=area_kitchen.id)

    area_living_room = area_registry.async_create("living room")
    device_living_room = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("test", "living_room-device")},
    )
    device_registry.async_update_device(
        device_living_room.id, area_id=area_living_room.id
    )

    started_event = asyncio.Event()
    num_timers = 3
    num_started = 0

    @callback
    def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        nonlocal num_started

        if event_type == TimerEventType.STARTED:
            num_started += 1
            if num_started == num_timers:
                started_event.set()

    async_register_timer_handler(hass, device_kitchen.id, handle_timer)
    async_register_timer_handler(hass, device_living_room.id, handle_timer)

    # Start timers in different areas
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"name": {"value": "pizza"}, "minutes": {"value": 10}},
        device_id=device_kitchen.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"name": {"value": "tv"}, "minutes": {"value": 10}},
        device_id=device_living_room.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"name": {"value": "media"}, "minutes": {"value": 15}},
        device_id=device_living_room.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Wait for all timers to start
    async with asyncio.timeout(1):
        await started_event.wait()

    # Cancel all timers in kitchen
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_CANCEL_ALL_TIMERS,
        {"area": {"value": "kitchen"}},
        device_id=device_kitchen.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.speech_slots.get("canceled", 0) == 1
    assert result.speech_slots.get("area") == "kitchen"

    # No timers should be running in kitchen
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_TIMER_STATUS,
        {"area": {"value": "kitchen"}},
        device_id=device_kitchen.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 0

    # timers should be running in living room
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_TIMER_STATUS,
        {"area": {"value": "living room"}},
        device_id=device_living_room.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 2