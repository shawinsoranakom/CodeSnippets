async def test_adjust_sum_statistics_energy(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    external_metadata_extra: dict[str, str],
    external_metadata_extra_2: dict[str, Any],
    source,
    statistic_id,
) -> None:
    """Test adjusting statistics."""
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

    imported_metadata = (
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
                "state": pytest.approx(0.0),
                "sum": pytest.approx(2.0),
            },
            {
                "start": period2.timestamp(),
                "end": (period2 + timedelta(hours=1)).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": None,
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

    # Adjust previously inserted statistics in kWh
    await client.send_json_auto_id(
        {
            "type": "recorder/adjust_sum_statistics",
            "statistic_id": statistic_id,
            "start_time": period2.isoformat(),
            "adjustment": 1000.0,
            "adjustment_unit_of_measurement": "kWh",
        }
    )
    response = await client.receive_json()
    assert response["success"]

    await async_wait_recording_done(hass)
    stats = statistics_during_period(hass, zero, period="hour")
    assert stats == {
        statistic_id: [
            {
                "start": period1.timestamp(),
                "end": (period1 + timedelta(hours=1)).timestamp(),
                "max": pytest.approx(None),
                "mean": pytest.approx(None),
                "min": pytest.approx(None),
                "last_reset": None,
                "state": pytest.approx(0.0),
                "sum": pytest.approx(2.0),
            },
            {
                "start": period2.timestamp(),
                "end": (period2 + timedelta(hours=1)).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": None,
                "state": pytest.approx(1.0),
                "sum": pytest.approx(1003.0),
            },
        ]
    }

    # Adjust previously inserted statistics in MWh
    await client.send_json_auto_id(
        {
            "type": "recorder/adjust_sum_statistics",
            "statistic_id": statistic_id,
            "start_time": period2.isoformat(),
            "adjustment": 2.0,
            "adjustment_unit_of_measurement": "MWh",
        }
    )
    response = await client.receive_json()
    assert response["success"]

    await async_wait_recording_done(hass)
    stats = statistics_during_period(hass, zero, period="hour")
    assert stats == {
        statistic_id: [
            {
                "start": period1.timestamp(),
                "end": (period1 + timedelta(hours=1)).timestamp(),
                "max": pytest.approx(None),
                "mean": pytest.approx(None),
                "min": pytest.approx(None),
                "last_reset": None,
                "state": pytest.approx(0.0),
                "sum": pytest.approx(2.0),
            },
            {
                "start": period2.timestamp(),
                "end": (period2 + timedelta(hours=1)).timestamp(),
                "max": None,
                "mean": None,
                "min": None,
                "last_reset": None,
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3003.0),
            },
        ]
    }