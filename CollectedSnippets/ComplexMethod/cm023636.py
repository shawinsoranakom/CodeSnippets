async def test_daily_statistics_sum(
    hass: HomeAssistant,
    setup_recorder: None,
    caplog: pytest.LogCaptureFixture,
    timezone,
) -> None:
    """Test daily statistics."""
    await hass.config.async_set_time_zone(timezone)
    await async_wait_recording_done(hass)
    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    zero = dt_util.utcnow()
    period1 = dt_util.as_utc(dt_util.parse_datetime("2022-10-03 00:00:00"))
    period2 = dt_util.as_utc(dt_util.parse_datetime("2022-10-03 23:00:00"))
    period3 = dt_util.as_utc(dt_util.parse_datetime("2022-10-04 00:00:00"))
    period4 = dt_util.as_utc(dt_util.parse_datetime("2022-10-04 23:00:00"))
    period5 = dt_util.as_utc(dt_util.parse_datetime("2022-10-05 00:00:00"))
    period6 = dt_util.as_utc(dt_util.parse_datetime("2022-10-05 23:00:00"))

    external_statistics = (
        {
            "start": period1,
            "last_reset": None,
            "state": 0,
            "sum": 2,
        },
        {
            "start": period2,
            "last_reset": None,
            "state": 1,
            "sum": 3,
        },
        {
            "start": period3,
            "last_reset": None,
            "state": 2,
            "sum": 4,
        },
        {
            "start": period4,
            "last_reset": None,
            "state": 3,
            "sum": 5,
        },
        {
            "start": period5,
            "last_reset": None,
            "state": 4,
            "sum": 6,
        },
        {
            "start": period6,
            "last_reset": None,
            "state": 5,
            "sum": 7,
        },
    )
    external_metadata = {
        "has_sum": True,
        "mean_type": StatisticMeanType.NONE,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_energy_import",
        "unit_class": "energy",
        "unit_of_measurement": "kWh",
    }

    async_add_external_statistics(hass, external_metadata, external_statistics)
    await async_wait_recording_done(hass)
    stats = statistics_during_period(
        hass, zero, period="day", statistic_ids={"test:total_energy_import"}
    )
    day1_start = dt_util.as_utc(dt_util.parse_datetime("2022-10-03 00:00:00"))
    day1_end = dt_util.as_utc(dt_util.parse_datetime("2022-10-04 00:00:00"))
    day2_start = dt_util.as_utc(dt_util.parse_datetime("2022-10-04 00:00:00"))
    day2_end = dt_util.as_utc(dt_util.parse_datetime("2022-10-05 00:00:00"))
    day3_start = dt_util.as_utc(dt_util.parse_datetime("2022-10-05 00:00:00"))
    day3_end = dt_util.as_utc(dt_util.parse_datetime("2022-10-06 00:00:00"))
    expected_stats = {
        "test:total_energy_import": [
            {
                "start": day1_start.timestamp(),
                "end": day1_end.timestamp(),
                "last_reset": None,
                "state": 1.0,
                "sum": 3.0,
            },
            {
                "start": day2_start.timestamp(),
                "end": day2_end.timestamp(),
                "last_reset": None,
                "state": 3.0,
                "sum": 5.0,
            },
            {
                "start": day3_start.timestamp(),
                "end": day3_end.timestamp(),
                "last_reset": None,
                "state": 5.0,
                "sum": 7.0,
            },
        ]
    }
    assert stats == expected_stats

    # Get change
    stats = statistics_during_period(
        hass,
        start_time=period1,
        statistic_ids={"test:total_energy_import"},
        period="day",
        types={"change"},
    )
    assert stats == {
        "test:total_energy_import": [
            {
                "start": day1_start.timestamp(),
                "end": day1_end.timestamp(),
                "change": 3.0,
            },
            {
                "start": day2_start.timestamp(),
                "end": day2_end.timestamp(),
                "change": 2.0,
            },
            {
                "start": day3_start.timestamp(),
                "end": day3_end.timestamp(),
                "change": 2.0,
            },
        ]
    }

    # Get data with start during the first period
    stats = statistics_during_period(
        hass,
        start_time=period1 + timedelta(hours=1),
        statistic_ids={"test:total_energy_import"},
        period="day",
    )
    assert stats == expected_stats

    # Get data with end during the third period
    stats = statistics_during_period(
        hass,
        start_time=zero,
        end_time=period6 - timedelta(hours=1),
        statistic_ids={"test:total_energy_import"},
        period="day",
    )
    assert stats == expected_stats

    # Try to get data for entities which do not exist
    stats = statistics_during_period(
        hass,
        start_time=zero,
        statistic_ids={"not", "the", "same", "test:total_energy_import"},
        period="day",
    )
    assert stats == expected_stats

    # Use 5minute to ensure table switch works
    stats = statistics_during_period(
        hass,
        start_time=zero,
        statistic_ids=["test:total_energy_import", "with_other"],
        period="5minute",
    )
    assert stats == {}

    # Ensure future date has not data
    future = dt_util.as_utc(dt_util.parse_datetime("2221-11-01 00:00:00"))
    stats = statistics_during_period(
        hass, start_time=future, end_time=future, period="day"
    )
    assert stats == {}