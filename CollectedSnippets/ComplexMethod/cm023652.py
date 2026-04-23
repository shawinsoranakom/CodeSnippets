async def test_list_statistic_ids(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    units,
    attributes,
    display_unit,
    statistics_unit,
    unit_class,
) -> None:
    """Test list_statistic_ids."""
    now = get_start_time(dt_util.utcnow())
    has_mean = attributes["state_class"] == "measurement"
    mean_type = StatisticMeanType.ARITHMETIC if has_mean else StatisticMeanType.NONE
    has_sum = not has_mean

    hass.config.units = units
    await async_setup_component(hass, "sensor", {})
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "recorder/list_statistic_ids"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    hass.states.async_set(
        "sensor.test", 10, attributes=attributes, timestamp=now.timestamp()
    )
    await async_wait_recording_done(hass)

    await client.send_json_auto_id({"type": "recorder/list_statistic_ids"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == [
        {
            "statistic_id": "sensor.test",
            "display_unit_of_measurement": display_unit,
            "has_mean": has_mean,
            "mean_type": mean_type,
            "has_sum": has_sum,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": statistics_unit,
            "unit_class": unit_class,
        }
    ]

    do_adhoc_statistics(hass, start=now)
    await async_recorder_block_till_done(hass)
    # Remove the state, statistics will now be fetched from the database
    hass.states.async_remove("sensor.test")
    await hass.async_block_till_done()

    await client.send_json_auto_id({"type": "recorder/list_statistic_ids"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == [
        {
            "statistic_id": "sensor.test",
            "display_unit_of_measurement": display_unit,
            "has_mean": has_mean,
            "mean_type": mean_type,
            "has_sum": has_sum,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": statistics_unit,
            "unit_class": unit_class,
        }
    ]

    await client.send_json_auto_id(
        {"type": "recorder/list_statistic_ids", "statistic_type": "dogs"}
    )
    response = await client.receive_json()
    assert not response["success"]

    await client.send_json_auto_id(
        {"type": "recorder/list_statistic_ids", "statistic_type": "mean"}
    )
    response = await client.receive_json()
    assert response["success"]
    if has_mean:
        assert response["result"] == [
            {
                "statistic_id": "sensor.test",
                "display_unit_of_measurement": display_unit,
                "has_mean": has_mean,
                "mean_type": mean_type,
                "has_sum": has_sum,
                "name": None,
                "source": "recorder",
                "statistics_unit_of_measurement": statistics_unit,
                "unit_class": unit_class,
            }
        ]
    else:
        assert response["result"] == []

    await client.send_json_auto_id(
        {"type": "recorder/list_statistic_ids", "statistic_type": "sum"}
    )
    response = await client.receive_json()
    assert response["success"]
    if has_sum:
        assert response["result"] == [
            {
                "statistic_id": "sensor.test",
                "display_unit_of_measurement": display_unit,
                "has_mean": has_mean,
                "mean_type": mean_type,
                "has_sum": has_sum,
                "name": None,
                "source": "recorder",
                "statistics_unit_of_measurement": statistics_unit,
                "unit_class": unit_class,
            }
        ]
    else:
        assert response["result"] == []