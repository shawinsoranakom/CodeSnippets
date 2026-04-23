async def test_statistic_during_period_hole_circular_mean(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test statistic_during_period when there are holes in the data."""
    now = dt_util.utcnow()

    await async_recorder_block_till_done(hass)
    client = await hass_ws_client()

    zero = now
    start = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=-18)

    imported_stats: list[StatisticData] = [
        {
            "start": (start + timedelta(hours=3 * i)),
            "mean": (123.456 * i) % 360,
            "mean_weight": 1,
        }
        for i in range(6)
    ]

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
        "mean": _circular_mean_approx(imported_stats[:]),
        "max": None,
        "min": None,
        "change": None,
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
        "mean": _circular_mean_approx(imported_stats[:]),
        "max": None,
        "min": None,
        "change": None,
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
        "mean": _circular_mean_approx(imported_stats[:]),
        "max": None,
        "min": None,
        "change": None,
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
        "mean": _circular_mean_approx(imported_stats[1:4]),
        "max": None,
        "min": None,
        "change": None,
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
        "mean": _circular_mean_approx(imported_stats[1:4]),
        "max": None,
        "min": None,
        "change": None,
    }