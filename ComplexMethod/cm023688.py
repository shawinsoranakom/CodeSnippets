async def test_purge_old_events_purges_the_event_type_ids(
    hass: HomeAssistant, recorder_mock: Recorder
) -> None:
    """Test deleting old events purges event type ids."""
    utcnow = dt_util.utcnow()
    five_days_ago = utcnow - timedelta(days=5)
    eleven_days_ago = utcnow - timedelta(days=11)
    far_past = utcnow - timedelta(days=1000)

    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    def _insert_events():
        with session_scope(hass=hass) as session:
            event_type_test_auto_purge = EventTypes(event_type="EVENT_TEST_AUTOPURGE")
            event_type_test_purge = EventTypes(event_type="EVENT_TEST_PURGE")
            event_type_test = EventTypes(event_type="EVENT_TEST")
            event_type_unused = EventTypes(event_type="EVENT_TEST_UNUSED")
            session.add_all(
                (
                    event_type_test_auto_purge,
                    event_type_test_purge,
                    event_type_test,
                    event_type_unused,
                )
            )
            session.flush()
            for _ in range(5):
                for event_id in range(6):
                    if event_id < 2:
                        timestamp = eleven_days_ago
                        event_type = event_type_test_auto_purge
                    elif event_id < 4:
                        timestamp = five_days_ago
                        event_type = event_type_test_purge
                    else:
                        timestamp = utcnow
                        event_type = event_type_test

                    session.add(
                        Events(
                            event_type=None,
                            event_type_id=event_type.event_type_id,
                            time_fired_ts=timestamp.timestamp(),
                        )
                    )
            return recorder_mock.event_type_manager.get_many(
                [
                    "EVENT_TEST_AUTOPURGE",
                    "EVENT_TEST_PURGE",
                    "EVENT_TEST",
                    "EVENT_TEST_UNUSED",
                ],
                session,
            )

    event_type_to_id = await recorder_mock.async_add_executor_job(_insert_events)
    test_event_type_ids = event_type_to_id.values()
    with session_scope(hass=hass) as session:
        events = session.query(Events).where(
            Events.event_type_id.in_(test_event_type_ids)
        )
        event_types = session.query(EventTypes).where(
            EventTypes.event_type_id.in_(test_event_type_ids)
        )

        assert events.count() == 30
        assert event_types.count() == 4

    # run purge_old_data()
    finished = purge_old_data(
        recorder_mock,
        far_past,
        repack=False,
    )
    assert finished

    with session_scope(hass=hass) as session:
        events = session.query(Events).where(
            Events.event_type_id.in_(test_event_type_ids)
        )
        event_types = session.query(EventTypes).where(
            EventTypes.event_type_id.in_(test_event_type_ids)
        )
        assert events.count() == 30
        # We should remove the unused event type
        assert event_types.count() == 3

    assert "EVENT_TEST_UNUSED" not in recorder_mock.event_type_manager._id_map

    # we should only have 10 events left since
    # only one event type was recorded now
    finished = purge_old_data(
        recorder_mock,
        utcnow,
        repack=False,
    )
    assert finished

    with session_scope(hass=hass) as session:
        events = session.query(Events).where(
            Events.event_type_id.in_(test_event_type_ids)
        )
        event_types = session.query(EventTypes).where(
            EventTypes.event_type_id.in_(test_event_type_ids)
        )
        assert events.count() == 10
        assert event_types.count() == 1

    # Purge everything
    finished = purge_old_data(
        recorder_mock,
        utcnow + timedelta(seconds=1),
        repack=False,
    )
    assert finished

    with session_scope(hass=hass) as session:
        events = session.query(Events).where(
            Events.event_type_id.in_(test_event_type_ids)
        )
        event_types = session.query(EventTypes).where(
            EventTypes.event_type_id.in_(test_event_type_ids)
        )
        assert events.count() == 0
        assert event_types.count() == 0