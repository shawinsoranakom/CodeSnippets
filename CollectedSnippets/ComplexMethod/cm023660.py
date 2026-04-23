async def test_import_statistics(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    external_metadata_extra: dict[str, str],
    external_metadata_extra_2: dict[str, Any],
    unit_1: str,
    unit_2: str,
    unit_3: str,
    expected_unit_class: str | None,
    source: str,
    statistic_id: str,
) -> None:
    """Test importing statistics."""
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
            "unit_of_measurement": unit_1,
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
    stats = statistics_during_period(
        hass, zero, period="hour", statistic_ids={statistic_id}
    )
    assert stats == {
        statistic_id: [
            {
                "start": period1.timestamp(),
                "end": (period1 + timedelta(hours=1)).timestamp(),
                "last_reset": None,
                "state": pytest.approx(0.0),
                "sum": pytest.approx(2.0),
            },
            {
                "start": period2.timestamp(),
                "end": (period2 + timedelta(hours=1)).timestamp(),
                "last_reset": None,
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
        ]
    }
    statistic_ids = list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "display_unit_of_measurement": unit_1,
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "statistic_id": statistic_id,
            "name": "Total imported energy",
            "source": source,
            "statistics_unit_of_measurement": unit_1,
            "unit_class": expected_unit_class,
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
                "unit_class": expected_unit_class,
                "unit_of_measurement": unit_1,
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
                "start": period2.timestamp(),
                "end": (period2 + timedelta(hours=1)).timestamp(),
                "last_reset": None,
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
        ]
    }

    # Update the previously inserted statistics
    external_statistics = {
        "start": period1.isoformat(),
        "last_reset": None,
        "state": 5,
        "sum": 6,
    }

    await client.send_json_auto_id(
        {
            "type": "recorder/import_statistics",
            "metadata": imported_metadata | {"unit_of_measurement": unit_2},
            "stats": [external_statistics],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] is None

    await async_wait_recording_done(hass)
    stats = statistics_during_period(
        hass, zero, period="hour", statistic_ids={statistic_id}
    )
    assert stats == {
        statistic_id: [
            {
                "start": period1.timestamp(),
                "end": (period1 + timedelta(hours=1)).timestamp(),
                "last_reset": None,
                "state": pytest.approx(5.0),
                "sum": pytest.approx(6.0),
            },
            {
                "start": period2.timestamp(),
                "end": (period2 + timedelta(hours=1)).timestamp(),
                "last_reset": None,
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
        ]
    }
    statistic_ids = list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "display_unit_of_measurement": unit_2,
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "statistic_id": statistic_id,
            "name": "Total imported energy",
            "source": source,
            "statistics_unit_of_measurement": unit_2,
            "unit_class": expected_unit_class,
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
                "unit_class": expected_unit_class,
                "unit_of_measurement": unit_2,
            },
        )
    }

    # Update the previously inserted statistics
    external_statistics = {
        "start": period1.isoformat(),
        "max": 1,
        "mean": 2,
        "min": 3,
        "last_reset": None,
        "state": 4,
        "sum": 5,
    }

    await client.send_json_auto_id(
        {
            "type": "recorder/import_statistics",
            "metadata": imported_metadata | {"unit_of_measurement": unit_3},
            "stats": [external_statistics],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] is None

    await async_wait_recording_done(hass)
    stats = statistics_during_period(
        hass, zero, period="hour", statistic_ids={statistic_id}
    )
    assert stats == {
        statistic_id: [
            {
                "start": period1.timestamp(),
                "end": (period1 + timedelta(hours=1)).timestamp(),
                "last_reset": None,
                "state": pytest.approx(4.0),
                "sum": pytest.approx(5.0),
            },
            {
                "start": period2.timestamp(),
                "end": (period2 + timedelta(hours=1)).timestamp(),
                "last_reset": None,
                "state": pytest.approx(1.0),
                "sum": pytest.approx(3.0),
            },
        ]
    }
    statistic_ids = list_statistic_ids(hass)
    assert statistic_ids == [
        {
            "display_unit_of_measurement": unit_3,
            "has_mean": False,
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "statistic_id": statistic_id,
            "name": "Total imported energy",
            "source": source,
            "statistics_unit_of_measurement": unit_3,
            "unit_class": expected_unit_class,
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
                "unit_class": expected_unit_class,
                "unit_of_measurement": unit_3,
            },
        )
    }