async def test_statistics_during_period_in_the_past(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test statistics_during_period in the past."""
    await hass.config.async_set_time_zone("UTC")
    now = get_start_time(dt_util.utcnow())

    hass.config.units = US_CUSTOMARY_SYSTEM
    await async_setup_component(hass, "sensor", {})
    await async_recorder_block_till_done(hass)

    past = now - timedelta(days=3)

    with freeze_time(past):
        hass.states.async_set("sensor.test", 10, attributes=POWER_SENSOR_KW_ATTRIBUTES)
        await async_wait_recording_done(hass)

    sensor_state = hass.states.get("sensor.test")
    assert sensor_state.last_updated == past

    stats_top_of_hour = past.replace(minute=0, second=0, microsecond=0)
    stats_start = past.replace(minute=55)
    do_adhoc_statistics(hass, start=stats_start)
    await async_wait_recording_done(hass)

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "start_time": now.isoformat(),
            "end_time": now.isoformat(),
            "statistic_ids": ["sensor.test"],
            "period": "hour",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {}

    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "start_time": now.isoformat(),
            "statistic_ids": ["sensor.test"],
            "period": "5minute",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {}

    past = now - timedelta(days=3, hours=1)
    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "start_time": past.isoformat(),
            "statistic_ids": ["sensor.test"],
            "period": "5minute",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "sensor.test": [
            {
                "start": int(stats_start.timestamp() * 1000),
                "end": int((stats_start + timedelta(minutes=5)).timestamp() * 1000),
                "mean": pytest.approx(10),
                "min": pytest.approx(10),
                "max": pytest.approx(10),
                "last_reset": None,
            }
        ]
    }

    start_of_day = stats_top_of_hour.replace(hour=0, minute=0)
    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "start_time": stats_top_of_hour.isoformat(),
            "statistic_ids": ["sensor.test"],
            "period": "day",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "sensor.test": [
            {
                "start": int(start_of_day.timestamp() * 1000),
                "end": int((start_of_day + timedelta(days=1)).timestamp() * 1000),
                "mean": pytest.approx(10),
                "min": pytest.approx(10),
                "max": pytest.approx(10),
                "last_reset": None,
            }
        ]
    }

    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "start_time": now.isoformat(),
            "statistic_ids": ["sensor.test"],
            "period": "5minute",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {}