async def test_yearly_statistics_sum(
    hass: HomeAssistant,
    setup_recorder: None,
    caplog: pytest.LogCaptureFixture,
    timezone,
) -> None:
    """Test monthly statistics."""
    await hass.config.async_set_time_zone(timezone)
    await async_wait_recording_done(hass)
    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    zero = dt_util.utcnow()
    period1 = dt_util.as_utc(dt_util.parse_datetime("2020-01-01 00:00:00"))
    period2 = dt_util.as_utc(dt_util.parse_datetime("2020-12-31 23:00:00"))
    period3 = dt_util.as_utc(dt_util.parse_datetime("2021-01-01 00:00:00"))
    period4 = dt_util.as_utc(dt_util.parse_datetime("2021-12-31 23:00:00"))
    period5 = dt_util.as_utc(dt_util.parse_datetime("2022-01-01 00:00:00"))
    period6 = dt_util.as_utc(dt_util.parse_datetime("2022-12-31 23:00:00"))

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
        hass, zero, period="year", statistic_ids={"test:total_energy_import"}
    )
    yr2020_start = dt_util.as_utc(dt_util.parse_datetime("2020-01-01 00:00:00"))
    yr2020_end = dt_util.as_utc(dt_util.parse_datetime("2021-01-01 00:00:00"))
    yr2021_start = dt_util.as_utc(dt_util.parse_datetime("2021-01-01 00:00:00"))
    yr2021_end = dt_util.as_utc(dt_util.parse_datetime("2022-01-01 00:00:00"))
    yr2022_start = dt_util.as_utc(dt_util.parse_datetime("2022-01-01 00:00:00"))
    yr2022_end = dt_util.as_utc(dt_util.parse_datetime("2023-01-01 00:00:00"))
    expected_stats = {
        "test:total_energy_import": [
            {
                "start": yr2020_start.timestamp(),
                "end": yr2020_end.timestamp(),
                "last_reset": None,
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
            {
                "start": yr2021_start.timestamp(),
                "end": yr2021_end.timestamp(),
                "last_reset": None,
                "state": pytest.approx(3.0),
                "sum": pytest.approx(5.0),
            },
            {
                "start": yr2022_start.timestamp(),
                "end": yr2022_end.timestamp(),
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
        period="year",
        types={"change"},
    )
    assert stats == {
        "test:total_energy_import": [
            {
                "start": yr2020_start.timestamp(),
                "end": yr2020_end.timestamp(),
                "change": 3.0,
            },
            {
                "start": yr2021_start.timestamp(),
                "end": yr2021_end.timestamp(),
                "change": 2.0,
            },
            {
                "start": yr2022_start.timestamp(),
                "end": yr2022_end.timestamp(),
                "change": 2.0,
            },
        ]
    }
    # Get data with start during the first period
    stats = statistics_during_period(
        hass,
        start_time=period1 + timedelta(days=1),
        statistic_ids={"test:total_energy_import"},
        period="year",
    )
    assert stats == expected_stats

    # Get data with end during the third period
    stats = statistics_during_period(
        hass,
        start_time=zero,
        end_time=period6 - timedelta(days=1),
        statistic_ids={"test:total_energy_import"},
        period="year",
    )
    assert stats == expected_stats

    # Try to get data for entities which do not exist
    stats = statistics_during_period(
        hass,
        start_time=zero,
        statistic_ids={"not", "the", "same", "test:total_energy_import"},
        period="year",
    )
    assert stats == expected_stats

    # Get only sum
    stats = statistics_during_period(
        hass,
        start_time=zero,
        statistic_ids={"not", "the", "same", "test:total_energy_import"},
        period="year",
        types={"sum"},
    )
    assert stats == {
        "test:total_energy_import": [
            {
                "start": yr2020_start.timestamp(),
                "end": yr2020_end.timestamp(),
                "sum": pytest.approx(3.0),
            },
            {
                "start": yr2021_start.timestamp(),
                "end": yr2021_end.timestamp(),
                "sum": pytest.approx(5.0),
            },
            {
                "start": yr2022_start.timestamp(),
                "end": yr2022_end.timestamp(),
                "sum": pytest.approx(7.0),
            },
        ]
    }

    # Get only sum + convert units
    stats = statistics_during_period(
        hass,
        start_time=zero,
        statistic_ids={"not", "the", "same", "test:total_energy_import"},
        period="year",
        types={"sum"},
        units={"energy": "Wh"},
    )
    assert stats == {
        "test:total_energy_import": [
            {
                "start": yr2020_start.timestamp(),
                "end": yr2020_end.timestamp(),
                "sum": pytest.approx(3000.0),
            },
            {
                "start": yr2021_start.timestamp(),
                "end": yr2021_end.timestamp(),
                "sum": pytest.approx(5000.0),
            },
            {
                "start": yr2022_start.timestamp(),
                "end": yr2022_end.timestamp(),
                "sum": pytest.approx(7000.0),
            },
        ]
    }

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
        hass, start_time=future, end_time=future, period="year"
    )
    assert stats == {}