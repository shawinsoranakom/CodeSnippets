async def test_service_disable_events_not_recording(
    hass: HomeAssistant,
    setup_recorder: None,
) -> None:
    """Test that events are not recorded when recorder is disabled using service."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISABLE,
        {},
        blocking=True,
    )

    event_type = "EVENT_TEST"

    events = []

    @callback
    def event_listener(event):
        """Record events from eventbus."""
        if event.event_type == event_type:
            events.append(event)

    hass.bus.async_listen(MATCH_ALL, event_listener)

    event_data1 = {"test_attr": 5, "test_attr_10": "nice"}
    hass.bus.async_fire(event_type, event_data1)
    await async_wait_recording_done(hass)

    assert len(events) == 1
    event = events[0]

    with session_scope(hass=hass, read_only=True) as session:
        db_events = list(
            session.query(Events)
            .filter(Events.event_type_id.in_(select_event_type_ids((event_type,))))
            .outerjoin(EventTypes, (Events.event_type_id == EventTypes.event_type_id))
        )
        assert len(db_events) == 0

    await hass.services.async_call(
        DOMAIN,
        SERVICE_ENABLE,
        {},
        blocking=True,
    )

    event_data2 = {"attr_one": 5, "attr_two": "nice"}
    hass.bus.async_fire(event_type, event_data2)
    await async_wait_recording_done(hass)

    assert len(events) == 2
    assert events[0] != events[1]
    assert events[0].data != events[1].data

    db_events = []
    with session_scope(hass=hass, read_only=True) as session:
        for select_event, event_data, event_types in (
            session.query(Events, EventData, EventTypes)
            .filter(Events.event_type_id.in_(select_event_type_ids((event_type,))))
            .outerjoin(EventTypes, (Events.event_type_id == EventTypes.event_type_id))
            .outerjoin(EventData, Events.data_id == EventData.data_id)
        ):
            select_event = cast(Events, select_event)
            event_data = cast(EventData, event_data)
            event_types = cast(EventTypes, event_types)

            native_event = db_event_to_native(select_event)
            native_event.data = db_event_data_to_native(event_data)
            native_event.event_type = event_types.event_type
            db_events.append(native_event)

    assert len(db_events) == 1
    db_event = db_events[0]
    event = events[1]

    assert event.event_type == db_event.event_type
    assert event.data == db_event.data
    assert event.origin == db_event.origin
    assert event.time_fired.replace(microsecond=0) == db_event.time_fired.replace(
        microsecond=0
    )