async def test_statistic_during_period(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    offset: int,
) -> None:
    """Test statistic_during_period."""
    now = dt_util.utcnow()

    await async_recorder_block_till_done(hass)
    client = await hass_ws_client()

    zero = now
    start = zero.replace(minute=offset * 5, second=0, microsecond=0) + timedelta(
        hours=-3
    )

    imported_stats_5min = [
        {
            "start": (start + timedelta(minutes=5 * i)),
            "max": i * 2,
            "mean": i,
            "min": -76 + i * 2,
            "sum": i,
        }
        for i in range(39)
    ]
    imported_stats = []
    slice_end = 12 - offset
    imported_stats.append(
        {
            "start": imported_stats_5min[0]["start"].replace(minute=0),
            "max": max(stat["max"] for stat in imported_stats_5min[0:slice_end]),
            "mean": fmean(stat["mean"] for stat in imported_stats_5min[0:slice_end]),
            "min": min(stat["min"] for stat in imported_stats_5min[0:slice_end]),
            "sum": imported_stats_5min[slice_end - 1]["sum"],
        }
    )
    for i in range(2):
        slice_start = i * 12 + (12 - offset)
        slice_end = (i + 1) * 12 + (12 - offset)
        assert imported_stats_5min[slice_start]["start"].minute == 0
        imported_stats.append(
            {
                "start": imported_stats_5min[slice_start]["start"],
                "max": max(
                    stat["max"] for stat in imported_stats_5min[slice_start:slice_end]
                ),
                "mean": fmean(
                    stat["mean"] for stat in imported_stats_5min[slice_start:slice_end]
                ),
                "min": min(
                    stat["min"] for stat in imported_stats_5min[slice_start:slice_end]
                ),
                "sum": imported_stats_5min[slice_end - 1]["sum"],
            }
        )

    imported_metadata = {
        "has_sum": True,
        "mean_type": StatisticMeanType.ARITHMETIC,
        "name": "Total imported energy",
        "source": "recorder",
        "statistic_id": "sensor.test",
        "unit_class": "energy",
        "unit_of_measurement": "kWh",
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
        "max": max(stat["max"] for stat in imported_stats_5min[:]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[:]),
        "min": min(stat["min"] for stat in imported_stats_5min[:]),
        "change": imported_stats_5min[-1]["sum"] - imported_stats_5min[0]["sum"],
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
        "max": max(stat["max"] for stat in imported_stats_5min[:]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[:]),
        "min": min(stat["min"] for stat in imported_stats_5min[:]),
        "change": imported_stats_5min[-1]["sum"] - imported_stats_5min[0]["sum"],
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
        "max": max(stat["max"] for stat in imported_stats_5min[:]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[:]),
        "min": min(stat["min"] for stat in imported_stats_5min[:]),
        "change": imported_stats_5min[-1]["sum"] - imported_stats_5min[0]["sum"],
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
        "max": max(stat["max"] for stat in imported_stats_5min[26:]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[26:]),
        "min": min(stat["min"] for stat in imported_stats_5min[26:]),
        "change": imported_stats_5min[-1]["sum"] - imported_stats_5min[25]["sum"],
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
        "max": max(stat["max"] for stat in imported_stats_5min[26:]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[26:]),
        "min": min(stat["min"] for stat in imported_stats_5min[26:]),
        "change": imported_stats_5min[-1]["sum"] - imported_stats_5min[25]["sum"],
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
        "max": max(stat["max"] for stat in imported_stats_5min[:26]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[:26]),
        "min": min(stat["min"] for stat in imported_stats_5min[:26]),
        "change": imported_stats_5min[25]["sum"] - 0,
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
        "max": max(stat["max"] for stat in imported_stats_5min[26:32]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[26:32]),
        "min": min(stat["min"] for stat in imported_stats_5min[26:32]),
        "change": imported_stats_5min[31]["sum"] - imported_stats_5min[25]["sum"],
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
        "max": max(stat["max"] for stat in imported_stats_5min[24 - offset :]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[24 - offset :]),
        "min": min(stat["min"] for stat in imported_stats_5min[24 - offset :]),
        "change": imported_stats_5min[-1]["sum"]
        - imported_stats_5min[23 - offset]["sum"],
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
        "max": max(stat["max"] for stat in imported_stats_5min[24 - offset :]),
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[24 - offset :]),
        "min": min(stat["min"] for stat in imported_stats_5min[24 - offset :]),
        "change": imported_stats_5min[-1]["sum"]
        - imported_stats_5min[23 - offset]["sum"],
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
        "max": max(stat["max"] for stat in imported_stats_5min[slice_start:slice_end]),
        "mean": fmean(
            stat["mean"] for stat in imported_stats_5min[slice_start:slice_end]
        ),
        "min": min(stat["min"] for stat in imported_stats_5min[slice_start:slice_end]),
        "change": imported_stats_5min[slice_end - 1]["sum"]
        - imported_stats_5min[slice_start - 1]["sum"],
    }

    # Test we can get only selected types
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": "sensor.test",
            "types": ["max", "change"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "max": max(stat["max"] for stat in imported_stats_5min[:]),
        "change": imported_stats_5min[-1]["sum"] - imported_stats_5min[0]["sum"],
    }

    # Test we can convert units
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": "sensor.test",
            "units": {"energy": "MWh"},
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "max": max(stat["max"] for stat in imported_stats_5min[:]) / 1000,
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[:]) / 1000,
        "min": min(stat["min"] for stat in imported_stats_5min[:]) / 1000,
        "change": (imported_stats_5min[-1]["sum"] - imported_stats_5min[0]["sum"])
        / 1000,
    }

    # Test we can automatically convert units
    hass.states.async_set(
        "sensor.test",
        None,
        attributes=ENERGY_SENSOR_WH_ATTRIBUTES,
        timestamp=now.timestamp(),
    )
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "max": max(stat["max"] for stat in imported_stats_5min[:]) * 1000,
        "mean": fmean(stat["mean"] for stat in imported_stats_5min[:]) * 1000,
        "min": min(stat["min"] for stat in imported_stats_5min[:]) * 1000,
        "change": (imported_stats_5min[-1]["sum"] - imported_stats_5min[0]["sum"])
        * 1000,
    }
    with session_scope(hass=hass, read_only=True) as session:
        stats = get_latest_short_term_statistics_with_session(
            hass,
            session,
            {"sensor.test"},
            {"last_reset", "state", "sum"},
        )
    start = imported_stats_5min[-1]["start"].timestamp()
    end = start + (5 * 60)
    assert stats == {
        "sensor.test": [
            {
                "end": end,
                "last_reset": None,
                "start": start,
                "state": None,
                "sum": 38.0,
            }
        ]
    }