async def test_auto_purge(hass: HomeAssistant, setup_recorder: None) -> None:
    """Test periodic purge scheduling."""
    timezone = "Europe/Copenhagen"
    await hass.config.async_set_time_zone(timezone)
    tz = dt_util.get_time_zone(timezone)

    # Purging is scheduled to happen at 4:12am every day. Exercise this behavior by
    # firing time changed events and advancing the clock around this time. Pick an
    # arbitrary year in the future to avoid boundary conditions relative to the current
    # date.
    #
    # The clock is started at 4:15am then advanced forward below
    now = dt_util.utcnow()
    test_time = datetime(now.year + 2, 1, 1, 4, 15, 0, tzinfo=tz)
    await run_tasks_at_time(hass, test_time)

    with (
        patch(
            "homeassistant.components.recorder.purge.purge_old_data", return_value=True
        ) as purge_old_data,
        patch(
            "homeassistant.components.recorder.tasks.periodic_db_cleanups"
        ) as periodic_db_cleanups,
    ):
        assert len(purge_old_data.mock_calls) == 0
        assert len(periodic_db_cleanups.mock_calls) == 0

        # Advance one day, and the purge task should run
        test_time = test_time + timedelta(days=1)
        await run_tasks_at_time(hass, test_time)
        assert len(purge_old_data.mock_calls) == 1
        assert len(periodic_db_cleanups.mock_calls) == 1

        purge_old_data.reset_mock()
        periodic_db_cleanups.reset_mock()

        # Advance one day, and the purge task should run again
        test_time = test_time + timedelta(days=1)
        await run_tasks_at_time(hass, test_time)
        assert len(purge_old_data.mock_calls) == 1
        assert len(periodic_db_cleanups.mock_calls) == 1

        purge_old_data.reset_mock()
        periodic_db_cleanups.reset_mock()

        # Advance less than one full day.  The alarm should not yet fire.
        test_time = test_time + timedelta(hours=23)
        await run_tasks_at_time(hass, test_time)
        assert len(purge_old_data.mock_calls) == 0
        assert len(periodic_db_cleanups.mock_calls) == 0

        # Advance to the next day and fire the alarm again
        test_time = test_time + timedelta(hours=1)
        await run_tasks_at_time(hass, test_time)
        assert len(purge_old_data.mock_calls) == 1
        assert len(periodic_db_cleanups.mock_calls) == 1