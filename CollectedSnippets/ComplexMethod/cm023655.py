async def test_update_statistics_metadata(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    requested_new_unit,
    websocket_command_extra,
    new_unit,
    new_unit_class,
    new_display_unit,
) -> None:
    """Test removing statistics."""
    now = get_start_time(dt_util.utcnow())

    units = METRIC_SYSTEM
    attributes = POWER_SENSOR_KW_ATTRIBUTES | {"device_class": None}
    state = 10

    hass.config.units = units
    await async_setup_component(hass, "sensor", {})
    await async_recorder_block_till_done(hass)
    hass.states.async_set(
        "sensor.test", state, attributes=attributes, timestamp=now.timestamp()
    )
    await async_wait_recording_done(hass)

    do_adhoc_statistics(hass, period="hourly", start=now)
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()

    await client.send_json_auto_id({"type": "recorder/list_statistic_ids"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == [
        {
            "statistic_id": "sensor.test",
            "display_unit_of_measurement": "kW",
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": "kW",
            "unit_class": "power",
        }
    ]

    await client.send_json_auto_id(
        {
            "type": "recorder/update_statistics_metadata",
            "statistic_id": "sensor.test",
            "unit_of_measurement": requested_new_unit,
        }
        | websocket_command_extra
    )
    response = await client.receive_json()
    assert response["success"]
    await async_recorder_block_till_done(hass)

    await client.send_json_auto_id({"type": "recorder/list_statistic_ids"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == [
        {
            "statistic_id": "sensor.test",
            "display_unit_of_measurement": new_display_unit,
            "has_mean": True,
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": new_unit,
            "unit_class": new_unit_class,
        }
    ]

    await client.send_json_auto_id(
        {
            "type": "recorder/statistics_during_period",
            "start_time": now.isoformat(),
            "statistic_ids": ["sensor.test"],
            "period": "5minute",
            "units": {"power": "W"},
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "sensor.test": [
            {
                "end": int((now + timedelta(minutes=5)).timestamp() * 1000),
                "last_reset": None,
                "max": 10.0,
                "mean": 10.0,
                "min": 10.0,
                "start": int(now.timestamp() * 1000),
            }
        ],
    }