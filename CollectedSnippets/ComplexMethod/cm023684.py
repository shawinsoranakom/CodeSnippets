async def test_purge_filtered_states_multiple_rounds(
    hass: HomeAssistant,
    recorder_mock: Recorder,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test filtered states are purged when there are multiple rounds to purge."""
    assert recorder_mock.entity_filter("sensor.excluded") is False

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
            # Add state **without** state_changed event that should be purged
            timestamp = dt_util.utcnow() - timedelta(days=1)
            session.add(
                States(
                    entity_id="sensor.excluded",
                    state="purgeme",
                    attributes="{}",
                    last_changed_ts=timestamp.timestamp(),
                    last_updated_ts=timestamp.timestamp(),
                )
            )
            # Add states and state_changed events that should be keeped
            timestamp = dt_util.utcnow() - timedelta(days=2)
            for event_id in range(200, 210):
                _add_state_with_state_attributes(
                    session,
                    "sensor.keep",
                    "keep",
                    timestamp,
                    event_id,
                )
            # Add states with linked old_state_ids that need to be handled
            timestamp = dt_util.utcnow() - timedelta(days=0)
            state_attrs = StateAttributes(
                hash=0,
                shared_attrs=json.dumps(
                    {"sensor.linked_old_state_id": "sensor.linked_old_state_id"}
                ),
            )
            state_1 = States(
                entity_id="sensor.linked_old_state_id",
                state="keep",
                attributes="{}",
                last_changed_ts=timestamp.timestamp(),
                last_updated_ts=timestamp.timestamp(),
                old_state_id=1,
                state_attributes=state_attrs,
            )
            timestamp = dt_util.utcnow() - timedelta(days=4)
            state_2 = States(
                entity_id="sensor.linked_old_state_id",
                state="keep",
                attributes="{}",
                last_changed_ts=timestamp.timestamp(),
                last_updated_ts=timestamp.timestamp(),
                old_state_id=2,
                state_attributes=state_attrs,
            )
            state_3 = States(
                entity_id="sensor.linked_old_state_id",
                state="keep",
                attributes="{}",
                last_changed_ts=timestamp.timestamp(),
                last_updated_ts=timestamp.timestamp(),
                old_state_id=62,  # keep
                state_attributes=state_attrs,
            )
            session.add_all((state_attrs, state_1, state_2, state_3))
            # Add event that should be keeped
            session.add(
                Events(
                    event_id=100,
                    event_type="EVENT_KEEP",
                    event_data="{}",
                    origin="LOCAL",
                    time_fired_ts=timestamp.timestamp(),
                )
            )
            convert_pending_states_to_meta(recorder_mock, session)
            convert_pending_events_to_event_types(recorder_mock, session)

    service_data = {"keep_days": 10, "apply_filter": True}
    _add_db_entries(hass)

    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 74
        events_keep = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(("EVENT_KEEP",)))
        )
        assert events_keep.count() == 1

    await hass.services.async_call(DOMAIN, SERVICE_PURGE, service_data, blocking=True)

    for _ in range(2):
        # Make sure the second round of purging runs
        await async_recorder_block_till_done(hass)
        await async_wait_purge_done(hass)

    assert "Cleanup filtered data hasn't fully completed yet" in caplog.text
    caplog.clear()

    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 13
        events_keep = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(("EVENT_KEEP",)))
        )
        assert events_keep.count() == 1

        states_sensor_excluded = (
            session.query(States)
            .outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
            .filter(StatesMeta.entity_id == "sensor.excluded")
        )
        assert states_sensor_excluded.count() == 0
        query = session.query(States)

        assert query.filter(States.state_id == 72).first().old_state_id is None
        assert query.filter(States.state_id == 72).first().attributes_id == 71
        assert query.filter(States.state_id == 73).first().old_state_id is None
        assert query.filter(States.state_id == 73).first().attributes_id == 71

        final_keep_state = session.query(States).filter(States.state_id == 74).first()
        assert final_keep_state.old_state_id == 62  # should have been kept
        assert final_keep_state.attributes_id == 71

        assert session.query(StateAttributes).count() == 11

    # Do it again to make sure nothing changes
    await hass.services.async_call(DOMAIN, SERVICE_PURGE, service_data)
    await async_recorder_block_till_done(hass)
    await async_wait_purge_done(hass)

    with session_scope(hass=hass) as session:
        final_keep_state = session.query(States).filter(States.state_id == 74).first()
        assert final_keep_state.old_state_id == 62  # should have been kept
        assert final_keep_state.attributes_id == 71

        assert session.query(StateAttributes).count() == 11

    for _ in range(2):
        # Make sure the second round of purging runs
        await async_recorder_block_till_done(hass)
        await async_wait_purge_done(hass)

    assert "Cleanup filtered data hasn't fully completed yet" not in caplog.text