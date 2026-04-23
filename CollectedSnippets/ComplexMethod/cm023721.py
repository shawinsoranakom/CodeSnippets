async def test_purge_method(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    use_sqlite: bool,
) -> None:
    """Test purge method."""

    def assert_recorder_runs_equal(run1, run2):
        assert run1.run_id == run2.run_id
        assert run1.start == run2.start
        assert run1.end == run2.end
        assert run1.closed_incorrect == run2.closed_incorrect
        assert run1.created == run2.created

    def assert_statistic_runs_equal(run1, run2):
        assert run1.run_id == run2.run_id
        assert run1.start == run2.start

    await async_attach_db_engine(hass)

    service_data = {"keep_days": 4}
    await _add_test_events(hass)
    await _add_test_states(hass)
    await _add_test_statistics(hass)
    await _add_test_recorder_runs(hass)
    await _add_test_statistics_runs(hass)
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    # make sure we start with 6 states
    with session_scope(hass=hass) as session:
        states = session.query(States)
        assert states.count() == 6

        events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
        assert events.count() == 6

        statistics = session.query(StatisticsShortTerm)
        assert statistics.count() == 6

        recorder_runs = session.query(RecorderRuns)
        assert recorder_runs.count() == 7
        runs_before_purge = recorder_runs.all()

        statistics_runs = session.query(StatisticsRuns).order_by(StatisticsRuns.run_id)
        assert statistics_runs.count() == 7
        statistic_runs_before_purge = statistics_runs.all()

        for itm in runs_before_purge:
            session.expunge(itm)
        for itm in statistic_runs_before_purge:
            session.expunge(itm)

    await hass.async_block_till_done()
    await async_wait_purge_done(hass)

    # run purge method - no service data, use defaults
    await hass.services.async_call("recorder", "purge")
    await hass.async_block_till_done()

    # Small wait for recorder thread
    await async_wait_purge_done(hass)

    with session_scope(hass=hass) as session:
        states = session.query(States)
        events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
        statistics = session.query(StatisticsShortTerm)

        # only purged old states, events and statistics
        assert states.count() == 4
        assert events.count() == 4
        assert statistics.count() == 4

    # run purge method - correct service data
    await hass.services.async_call("recorder", "purge", service_data=service_data)
    await hass.async_block_till_done()

    # Small wait for recorder thread
    await async_wait_purge_done(hass)

    with session_scope(hass=hass) as session:
        states = session.query(States)
        events = session.query(Events).filter(Events.event_type.like("EVENT_TEST%"))
        statistics = session.query(StatisticsShortTerm)
        recorder_runs = session.query(RecorderRuns)
        statistics_runs = session.query(StatisticsRuns)

        # we should only have 2 states, events and statistics left after purging
        assert states.count() == 2
        assert events.count() == 2
        assert statistics.count() == 2

        # now we should only have 3 recorder runs left
        runs = recorder_runs.all()
        assert_recorder_runs_equal(runs[0], runs_before_purge[0])
        assert_recorder_runs_equal(runs[1], runs_before_purge[5])
        assert_recorder_runs_equal(runs[2], runs_before_purge[6])

        # now we should only have 3 statistics runs left
        runs = statistics_runs.all()
        assert_statistic_runs_equal(runs[0], statistic_runs_before_purge[0])
        assert_statistic_runs_equal(runs[1], statistic_runs_before_purge[5])
        assert_statistic_runs_equal(runs[2], statistic_runs_before_purge[6])

        assert "EVENT_TEST_PURGE" not in (event.event_type for event in events.all())

    # run purge method - correct service data, with repack
    service_data["repack"] = True
    await hass.services.async_call("recorder", "purge", service_data=service_data)
    await hass.async_block_till_done()
    await async_wait_purge_done(hass)
    assert (
        "Vacuuming SQL DB to free space" in caplog.text
        or "Optimizing SQL DB to free space" in caplog.text
    )