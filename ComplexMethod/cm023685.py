async def test_purge_filtered_events_state_changed(
    hass: HomeAssistant, recorder_mock: Recorder
) -> None:
    """Test filtered state_changed events are purged. This should also remove all states."""
    # Assert entity_id is NOT excluded
    assert recorder_mock.entity_filter("sensor.excluded") is False
    assert recorder_mock.entity_filter("sensor.old_format") is False
    assert recorder_mock.entity_filter("sensor.keep") is True
    assert "excluded_event" in recorder_mock.exclude_event_types

    def _add_db_entries(hass: HomeAssistant) -> None:
        with session_scope(hass=hass) as session:
            # Add states and state_changed events that should be purged
            for days in range(1, 4):
                timestamp = dt_util.utcnow() - timedelta(days=days)
                for event_id in range(1000, 1020):
                    _add_state_with_state_attributes(
                        session,
                        "sensor.excluded",
                        "purgeme",
                        timestamp,
                        event_id * days,
                    )
            # Add events that should be keeped
            timestamp = dt_util.utcnow() - timedelta(days=1)
            for event_id in range(200, 210):
                session.add(
                    Events(
                        event_id=event_id,
                        event_type="EVENT_KEEP",
                        event_data="{}",
                        origin="LOCAL",
                        time_fired_ts=timestamp.timestamp(),
                    )
                )
            # Add states with linked old_state_ids that need to be handled
            timestamp = dt_util.utcnow() - timedelta(days=0)
            state_1 = States(
                entity_id="sensor.linked_old_state_id",
                state="keep",
                attributes="{}",
                last_changed_ts=timestamp.timestamp(),
                last_updated_ts=timestamp.timestamp(),
                old_state_id=1,
            )
            timestamp = dt_util.utcnow() - timedelta(days=4)
            state_2 = States(
                entity_id="sensor.linked_old_state_id",
                state="keep",
                attributes="{}",
                last_changed_ts=timestamp.timestamp(),
                last_updated_ts=timestamp.timestamp(),
                old_state_id=2,
            )
            state_3 = States(
                entity_id="sensor.linked_old_state_id",
                state="keep",
                attributes="{}",
                last_changed_ts=timestamp.timestamp(),
                last_updated_ts=timestamp.timestamp(),
                old_state_id=62,  # keep
            )
            session.add_all((state_1, state_2, state_3))
            session.add(
                Events(
                    event_id=231,
                    event_type="excluded_event",
                    event_data="{}",
                    origin="LOCAL",
                    time_fired_ts=timestamp.timestamp(),
                )
            )
            session.add(
                States(
                    entity_id="sensor.old_format",
                    state="remove",
                    attributes="{}",
                    last_changed_ts=timestamp.timestamp(),
                    last_updated_ts=timestamp.timestamp(),
                )
            )
            convert_pending_events_to_event_types(recorder_mock, session)
            convert_pending_states_to_meta(recorder_mock, session)

    service_data = {"keep_days": 10, "apply_filter": True}
    _add_db_entries(hass)

    with session_scope(hass=hass) as session:
        events_keep = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(("EVENT_KEEP",)))
        )
        events_purge = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(("excluded_event",)))
        )
        states = session.query(States)

        assert events_keep.count() == 10
        assert events_purge.count() == 1
        assert states.count() == 64

    await hass.services.async_call(DOMAIN, SERVICE_PURGE, service_data)
    await hass.async_block_till_done()

    for _ in range(4):
        await async_recorder_block_till_done(hass)
        await async_wait_purge_done(hass)

    with session_scope(hass=hass) as session:
        events_keep = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(("EVENT_KEEP",)))
        )
        events_purge = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(("excluded_event",)))
        )
        states = session.query(States)

        assert events_keep.count() == 10
        assert events_purge.count() == 0
        assert states.count() == 3

        assert (
            session.query(States).filter(States.state_id == 61).first().old_state_id
            is None
        )
        assert (
            session.query(States).filter(States.state_id == 62).first().old_state_id
            is None
        )
        assert (
            session.query(States).filter(States.state_id == 63).first().old_state_id
            == 62
        )