async def test_import_statistics(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    external_metadata_extra: dict[str, str],
    external_metadata_extra_2: dict[str, Any],
    source,
    statistic_id,
    import_fn,
    last_reset_str,
) -> None:
    """Test importing statistics and inserting external statistics."""
    client = await hass_ws_client()

    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    zero = dt_util.utcnow()
    last_reset = dt_util.parse_datetime(last_reset_str) if last_reset_str else None
    last_reset_utc = dt_util.as_utc(last_reset) if last_reset else None
    period1 = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    period2 = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)

    external_statistics1 = {
        "start": period1,
        "last_reset": last_reset,
        "state": 0,
        "sum": 2,
    }
    external_statistics2 = {
        "start": period2,
        "last_reset": last_reset,
        "state": 1,
        "sum": 3,
    }

    external_metadata = (
        {
            "has_sum": True,
            "name": "Total imported energy",
            "source": source,
            "statistic_id": statistic_id,
            "unit_of_measurement": "kWh",
        }
        | external_metadata_extra
        | external_metadata_extra_2
    )

    import_fn(hass, external_metadata, (external_statistics1, external_statistics2))
    await async_wait_recording_done(hass)
    stats = statistics_during_period(
        hass, zero, period="hour", statistic_ids={statistic_id}
    )
    assert stats == {
        statistic_id: [
            {
                "start": process_timestamp(period1).timestamp(),
                "end": process_timestamp(period1 + timedelta(hours=1)).timestamp(),
                "last_reset": datetime_to_timestamp_or_none(last_reset_utc),
                "state": pytest.approx(0.0),
                "sum": pytest.approx(2.0),
            },
            {
                "start": process_timestamp(period2).timestamp(),
                "end": process_timestamp(period2 + timedelta(hours=1)).timestamp(),
                "last_reset": datetime_to_timestamp_or_none(last_reset_utc),
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
        ]
    }
    statistic_ids = list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "display_unit_of_measurement": "kWh",
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "statistic_id": statistic_id,
            "name": "Total imported energy",
            "source": source,
            "statistics_unit_of_measurement": "kWh",
            "unit_class": "energy",
        }
    ]
    metadata = get_metadata(hass, statistic_ids={statistic_id})
    assert metadata == {
        statistic_id: (
            1,
            {
                "has_mean": False,
                "mean_type": StatisticMeanType.NONE,
                "has_sum": True,
                "name": "Total imported energy",
                "source": source,
                "statistic_id": statistic_id,
                "unit_class": "energy",
                "unit_of_measurement": "kWh",
            },
        )
    }
    last_stats = get_last_statistics(
        hass,
        1,
        statistic_id,
        True,
        {"last_reset", "max", "mean", "min", "state", "sum"},
    )
    assert last_stats == {
        statistic_id: [
            {
                "start": process_timestamp(period2).timestamp(),
                "end": process_timestamp(period2 + timedelta(hours=1)).timestamp(),
                "last_reset": datetime_to_timestamp_or_none(last_reset_utc),
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
        ]
    }

    # Update the previously inserted statistics
    external_statistics = {
        "start": period1,
        "last_reset": None,
        "state": 5,
        "sum": 6,
    }
    import_fn(hass, external_metadata, (external_statistics,))
    await async_wait_recording_done(hass)
    stats = statistics_during_period(
        hass, zero, period="hour", statistic_ids={statistic_id}
    )
    assert stats == {
        statistic_id: [
            {
                "start": process_timestamp(period1).timestamp(),
                "end": process_timestamp(period1 + timedelta(hours=1)).timestamp(),
                "last_reset": None,
                "state": pytest.approx(5.0),
                "sum": pytest.approx(6.0),
            },
            {
                "start": process_timestamp(period2).timestamp(),
                "end": process_timestamp(period2 + timedelta(hours=1)).timestamp(),
                "last_reset": datetime_to_timestamp_or_none(last_reset_utc),
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
        ]
    }

    # Update the previously inserted statistics + rename
    external_statistics = {
        "start": period1,
        "max": 1,
        "mean": 2,
        "min": 3,
        "last_reset": last_reset,
        "state": 4,
        "sum": 5,
    }
    external_metadata["name"] = "Total imported energy renamed"
    import_fn(hass, external_metadata, (external_statistics,))
    await async_wait_recording_done(hass)
    statistic_ids = list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "display_unit_of_measurement": "kWh",
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "statistic_id": statistic_id,
            "name": "Total imported energy renamed",
            "source": source,
            "statistics_unit_of_measurement": "kWh",
            "unit_class": "energy",
        }
    ]
    metadata = get_metadata(hass, statistic_ids={statistic_id})
    assert metadata == {
        statistic_id: (
            1,
            {
                "has_mean": False,
                "mean_type": StatisticMeanType.NONE,
                "has_sum": True,
                "name": "Total imported energy renamed",
                "source": source,
                "statistic_id": statistic_id,
                "unit_class": "energy",
                "unit_of_measurement": "kWh",
            },
        )
    }
    stats = statistics_during_period(
        hass, zero, period="hour", statistic_ids={statistic_id}
    )
    assert stats == {
        statistic_id: [
            {
                "start": process_timestamp(period1).timestamp(),
                "end": process_timestamp(period1 + timedelta(hours=1)).timestamp(),
                "last_reset": datetime_to_timestamp_or_none(last_reset_utc),
                "state": pytest.approx(4.0),
                "sum": pytest.approx(5.0),
            },
            {
                "start": process_timestamp(period2).timestamp(),
                "end": process_timestamp(period2 + timedelta(hours=1)).timestamp(),
                "last_reset": datetime_to_timestamp_or_none(last_reset_utc),
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
        ]
    }

    # Adjust the statistics in a different unit
    await client.send_json_auto_id(
        {
            "type": "recorder/adjust_sum_statistics",
            "statistic_id": statistic_id,
            "start_time": period2.isoformat(),
            "adjustment": 1000.0,
            "adjustment_unit_of_measurement": "MWh",
        }
    )
    response = await client.receive_json()
    assert response["success"]

    await async_wait_recording_done(hass)
    stats = statistics_during_period(
        hass, zero, period="hour", statistic_ids={statistic_id}
    )
    assert stats == {
        statistic_id: [
            {
                "start": process_timestamp(period1).timestamp(),
                "end": process_timestamp(period1 + timedelta(hours=1)).timestamp(),
                "last_reset": datetime_to_timestamp_or_none(last_reset_utc),
                "state": pytest.approx(4.0),
                "sum": pytest.approx(5.0),
            },
            {
                "start": process_timestamp(period2).timestamp(),
                "end": process_timestamp(period2 + timedelta(hours=1)).timestamp(),
                "last_reset": datetime_to_timestamp_or_none(last_reset_utc),
                "state": pytest.approx(1.0),
                "sum": pytest.approx(1000 * 1000 + 3.0),
            },
        ]
    }