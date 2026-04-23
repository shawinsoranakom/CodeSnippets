async def test_statistic_during_period_hole(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test statistic_during_period when there are holes in the data."""
    now = dt_util.utcnow()

    await async_recorder_block_till_done(hass)
    client = await hass_ws_client()

    zero = now
    start = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=-18)

    imported_stats = [
        {
            "start": (start + timedelta(hours=3 * i)),
            "max": i * 2,
            "mean": i,
            "min": -76 + i * 2,
            "sum": i,
        }
        for i in range(6)
    ]

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
    await async_wait_recording_done(hass)

    # This should include imported_stats[:]
    await client.send_json_auto_id(
        {
            "type": "recorder/statistic_during_period",
            "statistic_id": "sensor.test",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "max": max(stat["max"] for stat in imported_stats[:]),
        "mean": fmean(stat["mean"] for stat in imported_stats[:]),
        "min": min(stat["min"] for stat in imported_stats[:]),
        "change": imported_stats[-1]["sum"] - imported_stats[0]["sum"],
    }

    # This should also include imported_stats[:]
    start_time = "2022-10-20T13:00:00+00:00"
    end_time = "2022-10-21T05:00:00+00:00"
    assert imported_stats[0]["start"].isoformat() == start_time
    assert imported_stats[-1]["start"].isoformat() < end_time
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
        "max": max(stat["max"] for stat in imported_stats[:]),
        "mean": fmean(stat["mean"] for stat in imported_stats[:]),
        "min": min(stat["min"] for stat in imported_stats[:]),
        "change": imported_stats[-1]["sum"] - imported_stats[0]["sum"],
    }

    # This should also include imported_stats[:]
    start_time = "2022-10-20T13:00:00+00:00"
    end_time = "2022-10-21T08:20:00+00:00"
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
        "max": max(stat["max"] for stat in imported_stats[:]),
        "mean": fmean(stat["mean"] for stat in imported_stats[:]),
        "min": min(stat["min"] for stat in imported_stats[:]),
        "change": imported_stats[-1]["sum"] - imported_stats[0]["sum"],
    }

    # This should include imported_stats[1:4]
    start_time = "2022-10-20T16:00:00+00:00"
    end_time = "2022-10-20T23:00:00+00:00"
    assert imported_stats[1]["start"].isoformat() == start_time
    assert imported_stats[3]["start"].isoformat() < end_time
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
        "max": max(stat["max"] for stat in imported_stats[1:4]),
        "mean": fmean(stat["mean"] for stat in imported_stats[1:4]),
        "min": min(stat["min"] for stat in imported_stats[1:4]),
        "change": imported_stats[3]["sum"] - imported_stats[1]["sum"],
    }

    # This should also include imported_stats[1:4]
    start_time = "2022-10-20T15:00:00+00:00"
    end_time = "2022-10-21T00:00:00+00:00"
    assert imported_stats[1]["start"].isoformat() > start_time
    assert imported_stats[3]["start"].isoformat() < end_time
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
        "max": max(stat["max"] for stat in imported_stats[1:4]),
        "mean": fmean(stat["mean"] for stat in imported_stats[1:4]),
        "min": min(stat["min"] for stat in imported_stats[1:4]),
        "change": imported_stats[3]["sum"] - imported_stats[1]["sum"],
    }