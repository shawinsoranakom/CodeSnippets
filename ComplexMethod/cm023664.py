async def test_adjust_sum_statistics_errors(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    state_unit,
    statistic_unit,
    unit_class,
    factor,
    valid_units,
    invalid_units,
) -> None:
    """Test incorrectly adjusting statistics."""
    statistic_id = "sensor.total_energy_import"
    source = "recorder"
    client = await hass_ws_client()

    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    zero = dt_util.utcnow()
    period1 = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    period2 = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)

    imported_statistics1 = {
        "start": period1.isoformat(),
        "last_reset": None,
        "state": 0,
        "sum": 2,
    }
    imported_statistics2 = {
        "start": period2.isoformat(),
        "last_reset": None,
        "state": 1,
        "sum": 3,
    }

    imported_metadata = {
        "has_sum": True,
        "mean_type": int(StatisticMeanType.NONE),
        "name": "Total imported energy",
        "source": source,
        "statistic_id": statistic_id,
        "unit_class": unit_class,
        "unit_of_measurement": statistic_unit,
    }

    await client.send_json_auto_id(
        {
            "type": "recorder/import_statistics",
            "metadata": imported_metadata,
            "stats": [imported_statistics1, imported_statistics2],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] is None

    await async_wait_recording_done(hass)
    stats = statistics_during_period(hass, zero, period="hour")
    assert stats == {
        statistic_id: [
            {
                "start": period1.timestamp(),
                "end": (period1 + timedelta(hours=1)).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": None,
                "state": pytest.approx(0.0 * factor),
                "sum": pytest.approx(2.0 * factor),
            },
            {
                "start": period2.timestamp(),
                "end": (period2 + timedelta(hours=1)).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": None,
                "state": pytest.approx(1.0 * factor),
                "sum": pytest.approx(3.0 * factor),
            },
        ]
    }
    previous_stats = stats
    statistic_ids = list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "display_unit_of_measurement": state_unit,
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "statistic_id": statistic_id,
            "name": "Total imported energy",
            "source": source,
            "statistics_unit_of_measurement": state_unit,
            "unit_class": unit_class,
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
                "unit_class": unit_class,
                "unit_of_measurement": state_unit,
            },
        )
    }

    # Try to adjust statistics
    await client.send_json_auto_id(
        {
            "type": "recorder/adjust_sum_statistics",
            "statistic_id": "sensor.does_not_exist",
            "start_time": period2.isoformat(),
            "adjustment": 1000.0,
            "adjustment_unit_of_measurement": statistic_unit,
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "unknown_statistic_id"

    await async_wait_recording_done(hass)
    stats = statistics_during_period(hass, zero, period="hour")
    assert stats == previous_stats

    for unit in invalid_units:
        await client.send_json_auto_id(
            {
                "type": "recorder/adjust_sum_statistics",
                "statistic_id": statistic_id,
                "start_time": period2.isoformat(),
                "adjustment": 1000.0,
                "adjustment_unit_of_measurement": unit,
            }
        )
        response = await client.receive_json()
        assert not response["success"]
        assert response["error"]["code"] == "invalid_units"

        await async_wait_recording_done(hass)
        stats = statistics_during_period(hass, zero, period="hour")
        assert stats == previous_stats

    for unit in valid_units:
        await client.send_json_auto_id(
            {
                "type": "recorder/adjust_sum_statistics",
                "statistic_id": statistic_id,
                "start_time": period2.isoformat(),
                "adjustment": 1000.0,
                "adjustment_unit_of_measurement": unit,
            }
        )
        response = await client.receive_json()
        assert response["success"]

        await async_wait_recording_done(hass)
        stats = statistics_during_period(hass, zero, period="hour")
        assert stats != previous_stats
        previous_stats = stats