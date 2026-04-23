async def test_auto_statistics(
    hass: HomeAssistant,
    setup_recorder: None,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test periodic statistics scheduling."""
    timezone = "Europe/Copenhagen"
    await hass.config.async_set_time_zone(timezone)
    tz = dt_util.get_time_zone(timezone)

    stats_5min = []
    stats_hourly = []

    @callback
    def async_5min_stats_updated_listener(event: Event) -> None:
        """Handle recorder 5 min stat updated."""
        stats_5min.append(event)

    @callback
    def async_hourly_stats_updated_listener(event: Event) -> None:
        """Handle recorder 5 min stat updated."""
        stats_hourly.append(event)

    # Statistics is scheduled to happen every 5 minutes. Exercise this behavior by
    # firing time changed events and advancing the clock around this time. Pick an
    # arbitrary year in the future to avoid boundary conditions relative to the current
    # date.
    #
    # The clock is started at 4:51am then advanced forward below
    now = dt_util.utcnow()
    test_time = datetime(now.year + 2, 1, 1, 4, 51, 0, tzinfo=tz)
    freezer.move_to(test_time.isoformat())
    await run_tasks_at_time(hass, test_time)

    hass.bus.async_listen(
        EVENT_RECORDER_5MIN_STATISTICS_GENERATED, async_5min_stats_updated_listener
    )
    hass.bus.async_listen(
        EVENT_RECORDER_HOURLY_STATISTICS_GENERATED, async_hourly_stats_updated_listener
    )

    real_compile_statistics = statistics.compile_statistics
    with patch(
        "homeassistant.components.recorder.statistics.compile_statistics",
        side_effect=real_compile_statistics,
        autospec=True,
    ) as compile_statistics:
        # Advance 5 minutes, and the statistics task should run
        test_time = test_time + timedelta(minutes=5)
        freezer.move_to(test_time.isoformat())
        await run_tasks_at_time(hass, test_time)
        assert len(compile_statistics.mock_calls) == 1
        assert len(stats_5min) == 1
        assert len(stats_hourly) == 0

        compile_statistics.reset_mock()

        # Advance 5 minutes, and the statistics task should run again
        test_time = test_time + timedelta(minutes=5, seconds=1)
        freezer.move_to(test_time.isoformat())
        await run_tasks_at_time(hass, test_time)
        assert len(compile_statistics.mock_calls) == 1
        assert len(stats_5min) == 2
        assert len(stats_hourly) == 1

        compile_statistics.reset_mock()

        # Advance less than 5 minutes. The task should not run.
        test_time = test_time + timedelta(minutes=3)
        freezer.move_to(test_time.isoformat())
        await run_tasks_at_time(hass, test_time)
        assert len(compile_statistics.mock_calls) == 0
        assert len(stats_5min) == 2
        assert len(stats_hourly) == 1

        # Advance 5 minutes, and the statistics task should run again
        test_time = test_time + timedelta(minutes=5, seconds=1)
        freezer.move_to(test_time.isoformat())
        await run_tasks_at_time(hass, test_time)
        assert len(compile_statistics.mock_calls) == 1
        assert len(stats_5min) == 3
        assert len(stats_hourly) == 1