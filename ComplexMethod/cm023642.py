async def test_change(
    hass: HomeAssistant,
    setup_recorder: None,
    caplog: pytest.LogCaptureFixture,
    timezone,
) -> None:
    """Test deriving change from sum statistic."""
    await hass.config.async_set_time_zone(timezone)
    await async_wait_recording_done(hass)
    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    zero = dt_util.utcnow()
    period1 = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 00:00:00"))
    period2 = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 01:00:00"))
    period3 = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 02:00:00"))
    period4 = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 03:00:00"))

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
            "sum": 5,
        },
        {
            "start": period4,
            "last_reset": None,
            "state": 3,
            "sum": 8,
        },
    )
    external_metadata = {
        "has_sum": True,
        "mean_type": StatisticMeanType.NONE,
        "name": "Total imported energy",
        "source": "recorder",
        "statistic_id": "sensor.total_energy_import",
        "unit_class": "energy",
        "unit_of_measurement": "kWh",
    }

    async_import_statistics(hass, external_metadata, external_statistics)
    await async_wait_recording_done(hass)
    # Get change from far in the past
    stats = statistics_during_period(
        hass,
        zero,
        period="hour",
        statistic_ids={"sensor.total_energy_import"},
        types={"change"},
    )
    hour1_start = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 00:00:00"))
    hour1_end = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 01:00:00"))
    hour2_start = hour1_end
    hour2_end = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 02:00:00"))
    hour3_start = hour2_end
    hour3_end = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 03:00:00"))
    hour4_start = hour3_end
    hour4_end = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 04:00:00"))
    expected_stats = {
        "sensor.total_energy_import": [
            {
                "start": hour1_start.timestamp(),
                "end": hour1_end.timestamp(),
                "change": 2.0,
            },
            {
                "start": hour2_start.timestamp(),
                "end": hour2_end.timestamp(),
                "change": 1.0,
            },
            {
                "start": hour3_start.timestamp(),
                "end": hour3_end.timestamp(),
                "change": 2.0,
            },
            {
                "start": hour4_start.timestamp(),
                "end": hour4_end.timestamp(),
                "change": 3.0,
            },
        ]
    }
    assert stats == expected_stats

    # Get change + sum from far in the past
    stats = statistics_during_period(
        hass,
        zero,
        period="hour",
        statistic_ids={"sensor.total_energy_import"},
        types={"change", "sum"},
    )
    hour1_start = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 00:00:00"))
    hour1_end = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 01:00:00"))
    hour2_start = hour1_end
    hour2_end = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 02:00:00"))
    hour3_start = hour2_end
    hour3_end = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 03:00:00"))
    hour4_start = hour3_end
    hour4_end = dt_util.as_utc(dt_util.parse_datetime("2023-05-08 04:00:00"))
    expected_stats_change_sum = {
        "sensor.total_energy_import": [
            {
                "start": hour1_start.timestamp(),
                "end": hour1_end.timestamp(),
                "change": 2.0,
                "sum": 2.0,
            },
            {
                "start": hour2_start.timestamp(),
                "end": hour2_end.timestamp(),
                "change": 1.0,
                "sum": 3.0,
            },
            {
                "start": hour3_start.timestamp(),
                "end": hour3_end.timestamp(),
                "change": 2.0,
                "sum": 5.0,
            },
            {
                "start": hour4_start.timestamp(),
                "end": hour4_end.timestamp(),
                "change": 3.0,
                "sum": 8.0,
            },
        ]
    }
    assert stats == expected_stats_change_sum

    # Get change from far in the past with unit conversion
    stats = statistics_during_period(
        hass,
        start_time=hour1_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
        units={"energy": "Wh"},
    )
    expected_stats_wh = {
        "sensor.total_energy_import": [
            {
                "start": hour1_start.timestamp(),
                "end": hour1_end.timestamp(),
                "change": 2.0 * 1000,
            },
            {
                "start": hour2_start.timestamp(),
                "end": hour2_end.timestamp(),
                "change": 1.0 * 1000,
            },
            {
                "start": hour3_start.timestamp(),
                "end": hour3_end.timestamp(),
                "change": 2.0 * 1000,
            },
            {
                "start": hour4_start.timestamp(),
                "end": hour4_end.timestamp(),
                "change": 3.0 * 1000,
            },
        ]
    }
    assert stats == expected_stats_wh

    # Get change from far in the past with implicit unit conversion
    hass.states.async_set(
        "sensor.total_energy_import", "unknown", {"unit_of_measurement": "MWh"}
    )
    stats = statistics_during_period(
        hass,
        start_time=hour1_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
    )
    expected_stats_mwh = {
        "sensor.total_energy_import": [
            {
                "start": hour1_start.timestamp(),
                "end": hour1_end.timestamp(),
                "change": 2.0 / 1000,
            },
            {
                "start": hour2_start.timestamp(),
                "end": hour2_end.timestamp(),
                "change": 1.0 / 1000,
            },
            {
                "start": hour3_start.timestamp(),
                "end": hour3_end.timestamp(),
                "change": 2.0 / 1000,
            },
            {
                "start": hour4_start.timestamp(),
                "end": hour4_end.timestamp(),
                "change": 3.0 / 1000,
            },
        ]
    }
    assert stats == expected_stats_mwh
    hass.states.async_remove("sensor.total_energy_import")

    # Get change from the first recorded hour
    stats = statistics_during_period(
        hass,
        start_time=hour1_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
    )
    assert stats == expected_stats

    # Get change from the first recorded hour with unit conversion
    stats = statistics_during_period(
        hass,
        start_time=hour1_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
        units={"energy": "Wh"},
    )
    assert stats == expected_stats_wh

    # Get change from the first recorded hour with implicit unit conversion
    hass.states.async_set(
        "sensor.total_energy_import", "unknown", {"unit_of_measurement": "MWh"}
    )
    stats = statistics_during_period(
        hass,
        start_time=hour1_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
    )
    assert stats == expected_stats_mwh
    hass.states.async_remove("sensor.total_energy_import")

    # Get change from the second recorded hour
    stats = statistics_during_period(
        hass,
        start_time=hour2_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
    )
    assert stats == {
        "sensor.total_energy_import": expected_stats["sensor.total_energy_import"][1:4]
    }

    # Get change from the second recorded hour with unit conversion
    stats = statistics_during_period(
        hass,
        start_time=hour2_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
        units={"energy": "Wh"},
    )
    assert stats == {
        "sensor.total_energy_import": expected_stats_wh["sensor.total_energy_import"][
            1:4
        ]
    }

    # Get change from the second recorded hour with implicit unit conversion
    hass.states.async_set(
        "sensor.total_energy_import", "unknown", {"unit_of_measurement": "MWh"}
    )
    stats = statistics_during_period(
        hass,
        start_time=hour2_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
    )
    assert stats == {
        "sensor.total_energy_import": expected_stats_mwh["sensor.total_energy_import"][
            1:4
        ]
    }
    hass.states.async_remove("sensor.total_energy_import")

    # Get change from the second until the third recorded hour
    stats = statistics_during_period(
        hass,
        start_time=hour2_start,
        end_time=hour4_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
    )
    assert stats == {
        "sensor.total_energy_import": expected_stats["sensor.total_energy_import"][1:3]
    }

    # Get change from the fourth recorded hour
    stats = statistics_during_period(
        hass,
        start_time=hour4_start,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
    )
    assert stats == {
        "sensor.total_energy_import": expected_stats["sensor.total_energy_import"][3:4]
    }

    # Test change with a far future start date
    future = dt_util.as_utc(dt_util.parse_datetime("2221-11-01 00:00:00"))
    stats = statistics_during_period(
        hass,
        start_time=future,
        statistic_ids={"sensor.total_energy_import"},
        period="hour",
        types={"change"},
    )
    assert stats == {}