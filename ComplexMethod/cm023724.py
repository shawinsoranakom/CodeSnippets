async def test_purge_can_mix_legacy_and_new_format(
    hass: HomeAssistant, recorder_mock: Recorder
) -> None:
    """Test purging with legacy and new events."""
    await async_attach_db_engine(hass)

    await async_wait_recording_done(hass)
    # New databases are no longer created with the legacy events index
    assert recorder_mock.use_legacy_events_index is False

    def _recreate_legacy_events_index():
        """Recreate the legacy events index since its no longer created on new instances."""
        migration._create_index(
            recorder_mock, recorder_mock.get_session, "states", "ix_states_event_id"
        )
        recorder_mock.use_legacy_events_index = True

    await recorder_mock.async_add_executor_job(_recreate_legacy_events_index)
    assert recorder_mock.use_legacy_events_index is True

    utcnow = dt_util.utcnow()
    eleven_days_ago = utcnow - timedelta(days=11)

    with session_scope(hass=hass) as session:
        broken_state_no_time = States(
            event_id=None,
            entity_id="orphened.state",
            last_updated_ts=None,
            last_changed_ts=None,
        )
        session.add(broken_state_no_time)
        start_id = 50000
        for event_id in range(start_id, start_id + 50):
            _add_state_and_state_changed_event(
                session,
                "sensor.excluded",
                "purgeme",
                eleven_days_ago,
                event_id,
            )
    await _add_test_events(hass, 50)
    await _add_events_with_event_data(hass, 50)
    with session_scope(hass=hass) as session:
        for _ in range(50):
            _add_state_without_event_linkage(
                session, "switch.random", "on", eleven_days_ago
            )
        states_with_event_id = session.query(States).filter(
            States.event_id.is_not(None)
        )
        states_without_event_id = session.query(States).filter(
            States.event_id.is_(None)
        )

        assert states_with_event_id.count() == 50
        assert states_without_event_id.count() == 51

    purge_before = dt_util.utcnow() - timedelta(days=4)
    finished = purge_old_data(
        recorder_mock,
        purge_before,
        repack=False,
    )
    assert not finished

    with session_scope(hass=hass) as session:
        states_with_event_id = session.query(States).filter(
            States.event_id.is_not(None)
        )
        states_without_event_id = session.query(States).filter(
            States.event_id.is_(None)
        )
        assert states_with_event_id.count() == 0
        assert states_without_event_id.count() == 51

    # At this point all the legacy states are gone
    # and we switch methods
    purge_before = dt_util.utcnow() - timedelta(days=4)
    finished = purge_old_data(
        recorder_mock,
        purge_before,
        repack=False,
        events_batch_size=1,
        states_batch_size=1,
    )
    # Since we only allow one iteration, we won't
    # check if we are finished this loop similar
    # to the legacy method
    assert not finished

    with session_scope(hass=hass) as session:
        states_with_event_id = session.query(States).filter(
            States.event_id.is_not(None)
        )
        states_without_event_id = session.query(States).filter(
            States.event_id.is_(None)
        )
        assert states_with_event_id.count() == 0
        assert states_without_event_id.count() == 1

    finished = purge_old_data(
        recorder_mock,
        purge_before,
        repack=False,
        events_batch_size=100,
        states_batch_size=100,
    )
    assert finished

    with session_scope(hass=hass) as session:
        states_with_event_id = session.query(States).filter(
            States.event_id.is_not(None)
        )
        states_without_event_id = session.query(States).filter(
            States.event_id.is_(None)
        )
        assert states_with_event_id.count() == 0
        assert states_without_event_id.count() == 1
        _add_state_without_event_linkage(
            session, "switch.random", "on", eleven_days_ago
        )
        assert states_with_event_id.count() == 0
        assert states_without_event_id.count() == 2

    finished = purge_old_data(
        recorder_mock,
        purge_before,
        repack=False,
    )
    assert finished

    with session_scope(hass=hass) as session:
        states_with_event_id = session.query(States).filter(
            States.event_id.is_not(None)
        )
        states_without_event_id = session.query(States).filter(
            States.event_id.is_(None)
        )
        # The broken state without a timestamp
        # does not prevent future purges. Its ignored.
        assert states_with_event_id.count() == 0
        assert states_without_event_id.count() == 1