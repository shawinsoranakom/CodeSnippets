async def test_clear_statistics(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test removing statistics."""
    now = get_start_time(dt_util.utcnow())

    units = METRIC_SYSTEM
    attributes = POWER_SENSOR_KW_ATTRIBUTES
    state = 10
    value = 10

    hass.config.units = units
    await async_setup_component(hass, "sensor", {})
    await async_recorder_block_till_done(hass)
    hass.states.async_set(
        "sensor.test1", state, attributes=attributes, timestamp=now.timestamp()
    )
    hass.states.async_set(
        "sensor.test2", state * 2, attributes=attributes, timestamp=now.timestamp()
    )
    hass.states.async_set(
        "sensor.test3", state * 3, attributes=attributes, timestamp=now.timestamp()
    )
    await async_wait_recording_done(hass)

    do_adhoc_statistics(hass, start=now)
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "start_time": now.isoformat(),
            "statistic_ids": ["sensor.test1", "sensor.test2", "sensor.test3"],
            "period": "5minute",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expected_response = {
        "sensor.test1": [
            {
                "start": int(now.timestamp() * 1000),
                "end": int((now + timedelta(minutes=5)).timestamp() * 1000),
                "mean": pytest.approx(value),
                "min": pytest.approx(value),
                "max": pytest.approx(value),
                "last_reset": None,
            }
        ],
        "sensor.test2": [
            {
                "start": int(now.timestamp() * 1000),
                "end": int((now + timedelta(minutes=5)).timestamp() * 1000),
                "mean": pytest.approx(value * 2),
                "min": pytest.approx(value * 2),
                "max": pytest.approx(value * 2),
                "last_reset": None,
            }
        ],
        "sensor.test3": [
            {
                "start": int(now.timestamp() * 1000),
                "end": int((now + timedelta(minutes=5)).timestamp() * 1000),
                "mean": pytest.approx(value * 3),
                "min": pytest.approx(value * 3),
                "max": pytest.approx(value * 3),
                "last_reset": None,
            }
        ],
    }
    assert response["result"] == expected_response

    await client.send_json_auto_id(
        {
            "type": "recorder/clear_statistics",
            "statistic_ids": ["sensor.test"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "statistic_ids": ["sensor.test1", "sensor.test2", "sensor.test3"],
            "start_time": now.isoformat(),
            "period": "5minute",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == expected_response

    await client.send_json_auto_id(
        {
            "type": "recorder/clear_statistics",
            "statistic_ids": ["sensor.test1", "sensor.test3"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "statistic_ids": ["sensor.test1", "sensor.test2", "sensor.test3"],
            "start_time": now.isoformat(),
            "period": "5minute",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {"sensor.test2": expected_response["sensor.test2"]}