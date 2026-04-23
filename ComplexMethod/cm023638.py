async def test_weekly_statistics_mean(
    hass: HomeAssistant,
    setup_recorder: None,
    caplog: pytest.LogCaptureFixture,
    timezone,
) -> None:
    """Test weekly statistics."""
    await hass.config.async_set_time_zone(timezone)
    await async_wait_recording_done(hass)
    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    zero = dt_util.utcnow()
    period1 = dt_util.as_utc(dt_util.parse_datetime("2022-10-03 00:00:00"))
    period2 = dt_util.as_utc(dt_util.parse_datetime("2022-10-05 23:00:00"))
    period3 = dt_util.as_utc(dt_util.parse_datetime("2022-10-10 00:00:00"))
    period4 = dt_util.as_utc(dt_util.parse_datetime("2022-10-16 23:00:00"))

    external_statistics = (
        {
            "start": period1,
            "last_reset": None,
            "max": 0,
            "mean": 10,
            "min": -100,
        },
        {
            "start": period2,
            "last_reset": None,
            "max": 10,
            "mean": 20,
            "min": -90,
        },
        {
            "start": period3,
            "last_reset": None,
            "max": 20,
            "mean": 30,
            "min": -80,
        },
        {
            "start": period4,
            "last_reset": None,
            "max": 30,
            "mean": 40,
            "min": -70,
        },
    )
    external_metadata = {
        "has_sum": False,
        "mean_type": StatisticMeanType.ARITHMETIC,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_energy_import",
        "unit_class": "energy",
        "unit_of_measurement": "kWh",
    }

    async_add_external_statistics(hass, external_metadata, external_statistics)
    await async_wait_recording_done(hass)
    # Get all data
    stats = statistics_during_period(
        hass, zero, period="week", statistic_ids={"test:total_energy_import"}
    )
    week1_start = dt_util.as_utc(dt_util.parse_datetime("2022-10-03 00:00:00"))
    week1_end = dt_util.as_utc(dt_util.parse_datetime("2022-10-10 00:00:00"))
    week2_start = dt_util.as_utc(dt_util.parse_datetime("2022-10-10 00:00:00"))
    week2_end = dt_util.as_utc(dt_util.parse_datetime("2022-10-17 00:00:00"))
    expected_stats = {
        "test:total_energy_import": [
            {
                "start": week1_start.timestamp(),
                "end": week1_end.timestamp(),
                "last_reset": None,
                "max": 10,
                "mean": 15,
                "min": -100,
            },
            {
                "start": week2_start.timestamp(),
                "end": week2_end.timestamp(),
                "last_reset": None,
                "max": 30,
                "mean": 35,
                "min": -80,
            },
        ]
    }
    assert stats == expected_stats

    # Get data starting with start of the first period
    stats = statistics_during_period(
        hass,
        start_time=period1,
        statistic_ids={"test:total_energy_import"},
        period="week",
    )
    assert stats == expected_stats

    # Get data with start during the first period
    stats = statistics_during_period(
        hass,
        start_time=period1 + timedelta(days=1),
        statistic_ids={"test:total_energy_import"},
        period="week",
    )
    assert stats == expected_stats

    # Try to get data for entities which do not exist
    stats = statistics_during_period(
        hass,
        start_time=zero,
        statistic_ids={"not", "the", "same", "test:total_energy_import"},
        period="week",
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
        hass, start_time=future, end_time=future, period="week"
    )
    assert stats == {}