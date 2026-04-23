async def test_disambiguation(
    hass: HomeAssistant,
    init_components,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test finding a timer by disambiguating with area/floor."""
    entry = MockConfigEntry()
    entry.add_to_hass(hass)

    cancelled_event = asyncio.Event()
    timer_info: TimerInfo | None = None

    @callback
    def handle_timer(event_type: TimerEventType, timer: TimerInfo) -> None:
        nonlocal timer_info

        if event_type == TimerEventType.CANCELLED:
            timer_info = timer
            cancelled_event.set()

    # Alice is upstairs in the study
    floor_upstairs = floor_registry.async_create("upstairs")
    area_study = area_registry.async_create("study")
    area_study = area_registry.async_update(
        area_study.id, floor_id=floor_upstairs.floor_id
    )
    device_alice_study = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("test", "alice")},
    )
    device_registry.async_update_device(device_alice_study.id, area_id=area_study.id)

    # Bob is downstairs in the kitchen
    floor_downstairs = floor_registry.async_create("downstairs")
    area_kitchen = area_registry.async_create("kitchen")
    area_kitchen = area_registry.async_update(
        area_kitchen.id, floor_id=floor_downstairs.floor_id
    )
    device_bob_kitchen_1 = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("test", "bob")},
    )
    device_registry.async_update_device(
        device_bob_kitchen_1.id, area_id=area_kitchen.id
    )

    async_register_timer_handler(hass, device_alice_study.id, handle_timer)
    async_register_timer_handler(hass, device_bob_kitchen_1.id, handle_timer)

    # Alice: set a 3 minute timer
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"minutes": {"value": 3}},
        device_id=device_alice_study.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Bob: set a 3 minute timer
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"minutes": {"value": 3}},
        device_id=device_bob_kitchen_1.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Alice should hear her timer listed first
    result = await intent.async_handle(
        hass, "test", intent.INTENT_TIMER_STATUS, {}, device_id=device_alice_study.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 2
    assert timers[0].get(ATTR_DEVICE_ID) == device_alice_study.id
    assert timers[1].get(ATTR_DEVICE_ID) == device_bob_kitchen_1.id

    # Bob should hear his timer listed first
    result = await intent.async_handle(
        hass, "test", intent.INTENT_TIMER_STATUS, {}, device_id=device_bob_kitchen_1.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 2
    assert timers[0].get(ATTR_DEVICE_ID) == device_bob_kitchen_1.id
    assert timers[1].get(ATTR_DEVICE_ID) == device_alice_study.id

    # Alice: cancel my timer
    cancelled_event.clear()
    timer_info = None
    result = await intent.async_handle(
        hass, "test", intent.INTENT_CANCEL_TIMER, {}, device_id=device_alice_study.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await cancelled_event.wait()

    # Verify this is the 3 minute timer from Alice
    assert timer_info is not None
    assert timer_info.device_id == device_alice_study.id
    assert timer_info.start_minutes == 3

    # Cancel Bob's timer
    result = await intent.async_handle(
        hass, "test", intent.INTENT_CANCEL_TIMER, {}, device_id=device_bob_kitchen_1.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Add two new devices in two new areas, one upstairs and one downstairs
    area_bedroom = area_registry.async_create("bedroom")
    area_bedroom = area_registry.async_update(
        area_bedroom.id, floor_id=floor_upstairs.floor_id
    )
    device_alice_bedroom = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("test", "alice-2")},
    )
    device_registry.async_update_device(
        device_alice_bedroom.id, area_id=area_bedroom.id
    )

    area_living_room = area_registry.async_create("living_room")
    area_living_room = area_registry.async_update(
        area_living_room.id, floor_id=floor_downstairs.floor_id
    )
    device_bob_living_room = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("test", "bob-2")},
    )
    device_registry.async_update_device(
        device_bob_living_room.id, area_id=area_living_room.id
    )

    async_register_timer_handler(hass, device_alice_bedroom.id, handle_timer)
    async_register_timer_handler(hass, device_bob_living_room.id, handle_timer)

    # Alice: set a 3 minute timer (study)
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"minutes": {"value": 3}},
        device_id=device_alice_study.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Alice: set a 3 minute timer (bedroom)
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"minutes": {"value": 3}},
        device_id=device_alice_bedroom.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Bob: set a 3 minute timer (kitchen)
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"minutes": {"value": 3}},
        device_id=device_bob_kitchen_1.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Bob: set a 3 minute timer (living room)
    result = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_START_TIMER,
        {"minutes": {"value": 3}},
        device_id=device_bob_living_room.id,
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    # Alice should hear the timer in her area first, then on her floor, then
    # elsewhere.
    result = await intent.async_handle(
        hass, "test", intent.INTENT_TIMER_STATUS, {}, device_id=device_alice_study.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE
    timers = result.speech_slots.get("timers", [])
    assert len(timers) == 4
    assert timers[0].get(ATTR_DEVICE_ID) == device_alice_study.id
    assert timers[1].get(ATTR_DEVICE_ID) == device_alice_bedroom.id
    assert timers[2].get(ATTR_DEVICE_ID) == device_bob_kitchen_1.id
    assert timers[3].get(ATTR_DEVICE_ID) == device_bob_living_room.id

    # Alice cancels the study timer from study
    cancelled_event.clear()
    timer_info = None
    result = await intent.async_handle(
        hass, "test", intent.INTENT_CANCEL_TIMER, {}, device_id=device_alice_study.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await cancelled_event.wait()

    # Verify this is the 3 minute timer from Alice in the study
    assert timer_info is not None
    assert timer_info.device_id == device_alice_study.id
    assert timer_info.start_minutes == 3

    # Trying to cancel the remaining two timers from a disconnected area fails
    area_garage = area_registry.async_create("garage")
    device_garage = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("test", "garage")},
    )
    device_registry.async_update_device(device_garage.id, area_id=area_garage.id)
    async_register_timer_handler(hass, device_garage.id, handle_timer)

    with pytest.raises(MultipleTimersMatchedError):
        await intent.async_handle(
            hass,
            "test",
            intent.INTENT_CANCEL_TIMER,
            {},
            device_id=device_garage.id,
        )

    # Alice cancels the bedroom timer from study (same floor)
    cancelled_event.clear()
    timer_info = None
    result = await intent.async_handle(
        hass, "test", intent.INTENT_CANCEL_TIMER, {}, device_id=device_alice_study.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await cancelled_event.wait()

    # Verify this is the 3 minute timer from Alice in the bedroom
    assert timer_info is not None
    assert timer_info.device_id == device_alice_bedroom.id
    assert timer_info.start_minutes == 3

    # Add a second device in the kitchen
    device_bob_kitchen_2 = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("test", "bob-3")},
    )
    device_registry.async_update_device(
        device_bob_kitchen_2.id, area_id=area_kitchen.id
    )

    async_register_timer_handler(hass, device_bob_kitchen_2.id, handle_timer)

    # Bob cancels the kitchen timer from a different device
    cancelled_event.clear()
    timer_info = None
    result = await intent.async_handle(
        hass, "test", intent.INTENT_CANCEL_TIMER, {}, device_id=device_bob_kitchen_2.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await cancelled_event.wait()

    assert timer_info is not None
    assert timer_info.device_id == device_bob_kitchen_1.id
    assert timer_info.start_minutes == 3

    # Bob cancels the living room timer from the kitchen
    cancelled_event.clear()
    timer_info = None
    result = await intent.async_handle(
        hass, "test", intent.INTENT_CANCEL_TIMER, {}, device_id=device_bob_kitchen_2.id
    )
    assert result.response_type == intent.IntentResponseType.ACTION_DONE

    async with asyncio.timeout(1):
        await cancelled_event.wait()

    assert timer_info is not None
    assert timer_info.device_id == device_bob_living_room.id
    assert timer_info.start_minutes == 3