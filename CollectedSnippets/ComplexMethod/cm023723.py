async def test_purge_many_old_events(
    hass: HomeAssistant, recorder_mock: Recorder
) -> None:
    """Test deleting old events."""
    await async_attach_db_engine(hass)

    old_events_count = 5
    with (
        patch.object(recorder_mock, "max_bind_vars", old_events_count),
        patch.object(recorder_mock.database_engine, "max_bind_vars", old_events_count),
    ):
        await _add_test_events(hass, old_events_count)

        with session_scope(hass=hass) as session:
            events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
            assert events.count() == old_events_count * 6

        purge_before = dt_util.utcnow() - timedelta(days=4)

        # run purge_old_data()
        finished = purge_old_data(
            recorder_mock,
            purge_before,
            repack=False,
            states_batch_size=3,
            events_batch_size=3,
        )
        assert not finished

        with session_scope(hass=hass) as session:
            events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
            assert events.count() == old_events_count * 3

        # we should only have 2 groups of events left
        finished = purge_old_data(
            recorder_mock,
            purge_before,
            repack=False,
            states_batch_size=3,
            events_batch_size=3,
        )
        assert finished

        with session_scope(hass=hass) as session:
            events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
            assert events.count() == old_events_count * 2

        # we should now purge everything
        finished = purge_old_data(
            recorder_mock,
            dt_util.utcnow(),
            repack=False,
            states_batch_size=20,
            events_batch_size=20,
        )
        assert finished

        with session_scope(hass=hass) as session:
            events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
            assert events.count() == 0