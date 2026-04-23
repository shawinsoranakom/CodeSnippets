async def test_statistic_during_period_circular_mean(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    offset: int,
    step_size: float,
    tolerance: float,
) -> None:
    """Test statistic_during_period."""
    now = dt_util.utcnow()

    await async_recorder_block_till_done(hass)
    client = await hass_ws_client()

    zero = now
    start = zero.replace(minute=offset * 5, second=0, microsecond=0) + timedelta(
        hours=-3
    )

    imported_stats_5min: list[StatisticData] = [
        {
            "start": (start + timedelta(minutes=5 * i)),
            "mean": (step_size * i) % 360,
            "mean_weight": 1,
        }
        for i in range(39)
    ]

    imported_stats = []
    slice_end = 12 - offset
    imported_stats.append(
        {
            "start": imported_stats_5min[0]["start"].replace(minute=0),
            **_circular_mean(imported_stats_5min[0:slice_end]),
        }
    )
    for i in range(2):
        slice_start = i * 12 + (12 - offset)
        slice_end = (i + 1) * 12 + (12 - offset)
        assert imported_stats_5min[slice_start]["start"].minute == 0
        imported_stats.append(
            {
                "start": imported_stats_5min[slice_start]["start"],
                **_circular_mean(imported_stats_5min[slice_start:slice_end]),
            }
        )

    imported_metadata: StatisticMetaData = {
        "mean_type": StatisticMeanType.CIRCULAR,
        "has_sum": False,
        "name": "Wind direction",
        "source": "recorder",
        "statistic_id": "sensor.test",
        "unit_class": None,
        "unit_of_measurement": DEGREE,
    }

    recorder.get_instance(hass).async_import_statistics(
        imported_metadata,
        imported_stats,
        Statistics,
    )
    recorder.get_instance(hass).async_import_statistics(
        imported_metadata,
        imported_stats_5min,
        StatisticsShortTerm,
    )
    await async_wait_recording_done(hass)

    metadata = get_metadata(hass, statistic_ids={"sensor.test"})
    metadata_id = metadata["sensor.test"][0]
    run_cache = get_short_term_statistics_run_cache(hass)
    # Verify the import of the short term statistics
    # also updates the run cache
    assert run_cache.get_latest_ids({metadata_id}) is not None

    # No data for this period yet
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "fixed_period": {
                "start_time": now.isoformat(),
                "end_time": now.isoformat(),
            },
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "max": None,
        "mean": None,
        "min": None,
        "change": None,
    }

    # This should include imported_statistics_5min[:]
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min, tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should also include imported_statistics_5min[:]
    start_time = (
        dt_util.parse_datetime("2022-10-21T04:00:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    end_time = (
        dt_util.parse_datetime("2022-10-21T07:15:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": "sensor.test",
            "fixed_period": {
                "start_time": start_time,
                "end_time": end_time,
            },
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min, tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should also include imported_statistics_5min[:]
    start_time = (
        dt_util.parse_datetime("2022-10-21T04:00:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    end_time = (
        dt_util.parse_datetime("2022-10-21T08:20:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": "sensor.test",
            "fixed_period": {
                "start_time": start_time,
                "end_time": end_time,
            },
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min, tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should include imported_statistics_5min[26:]
    start_time = (
        dt_util.parse_datetime("2022-10-21T06:10:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    assert imported_stats_5min[26]["start"].isoformat() == start_time
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "fixed_period": {
                "start_time": start_time,
            },
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min[26:], tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should also include imported_statistics_5min[26:]
    start_time = (
        dt_util.parse_datetime("2022-10-21T06:09:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "fixed_period": {
                "start_time": start_time,
            },
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min[26:], tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should include imported_statistics_5min[:26]
    end_time = (
        dt_util.parse_datetime("2022-10-21T06:10:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    assert imported_stats_5min[26]["start"].isoformat() == end_time
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "fixed_period": {
                "end_time": end_time,
            },
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min[:26], tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should include imported_statistics_5min[26:32] (less than a full hour)
    start_time = (
        dt_util.parse_datetime("2022-10-21T06:10:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    assert imported_stats_5min[26]["start"].isoformat() == start_time
    end_time = (
        dt_util.parse_datetime("2022-10-21T06:40:00+00:00")
        + timedelta(minutes=5 * offset)
    ).isoformat()
    assert imported_stats_5min[32]["start"].isoformat() == end_time
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "fixed_period": {
                "start_time": start_time,
                "end_time": end_time,
            },
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min[26:32], tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should include imported_statistics[2:] + imported_statistics_5min[36:]
    start_time = "2022-10-21T06:00:00+00:00"
    assert imported_stats_5min[24 - offset]["start"].isoformat() == start_time
    assert imported_stats[2]["start"].isoformat() == start_time
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "fixed_period": {
                "start_time": start_time,
            },
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min[24 - offset :], tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should also include imported_statistics[2:] + imported_statistics_5min[36:]
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "rolling_window": {
                "duration": {"hours": 1, "minutes": 25},
            },
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min[24 - offset :], tolerance),
        "max": None,
        "min": None,
        "change": None,
    }

    # This should include imported_statistics[2:3]
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "rolling_window": {
                "duration": {"hours": 1},
                "offset": {"minutes": -25},
            },
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    slice_start = 24 - offset
    slice_end = 36 - offset
    assert response["result"] == {
        "mean": _circular_mean_approx(
            imported_stats_5min[slice_start:slice_end], tolerance
        ),
        "max": None,
        "min": None,
        "change": None,
    }

    # Test we can get only selected types
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": "sensor.test",
            "types": ["mean"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "mean": _circular_mean_approx(imported_stats_5min, tolerance),
    }