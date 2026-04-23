async def test_get_statistics_metadata(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    units,
    attributes,
    unit,
    unit_class,
) -> None:
    """Test get_statistics_metadata."""
    now = get_start_time(dt_util.utcnow())
    has_mean = attributes["state_class"] == "measurement"
    mean_type = StatisticMeanType.ARITHMETIC if has_mean else StatisticMeanType.NONE
    has_sum = not has_mean

    hass.config.units = units
    await async_setup_component(hass, "sensor", {})
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "recorder/get_statistics_metadata"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    period1 = dt_util.as_utc(dt_util.parse_datetime("2021-09-01 00:00:00"))
    period2 = dt_util.as_utc(dt_util.parse_datetime("2021-09-30 23:00:00"))
    period3 = dt_util.as_utc(dt_util.parse_datetime("2021-10-01 00:00:00"))
    period4 = dt_util.as_utc(dt_util.parse_datetime("2021-10-31 23:00:00"))
    external_energy_statistics_1 = (
        {
            "start": period1,
            "last_reset": None,
            "state": 0,
            "sum": 2,
        },
        {
            "start": period2,
            "last_reset": None,
            "state": 1,
            "sum": 3,
        },
        {
            "start": period3,
            "last_reset": None,
            "state": 2,
            "sum": 5,
        },
        {
            "start": period4,
            "last_reset": None,
            "state": 3,
            "sum": 8,
        },
    )
    external_energy_metadata_1 = {
        "has_sum": has_sum,
        "mean_type": mean_type,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_gas",
        "unit_class": unit_class,
        "unit_of_measurement": unit,
    }

    async_add_external_statistics(
        hass, external_energy_metadata_1, external_energy_statistics_1
    )
    await async_wait_recording_done(hass)

    await client.send_json_auto_id(
        {
            "type": "recorder/get_statistics_metadata",
            "statistic_ids": ["test:total_gas"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == [
        {
            "statistic_id": "test:total_gas",
            "display_unit_of_measurement": unit,
            "has_mean": has_mean,
            "mean_type": mean_type,
            "has_sum": has_sum,
            "name": "Total imported energy",
            "source": "test",
            "statistics_unit_of_measurement": unit,
            "unit_class": unit_class,
        }
    ]

    hass.states.async_set(
        "sensor.test", 10, attributes=attributes, timestamp=now.timestamp()
    )
    await async_wait_recording_done(hass)

    hass.states.async_set(
        "sensor.test2", 10, attributes=attributes, timestamp=now.timestamp()
    )
    await async_wait_recording_done(hass)

    await client.send_json_auto_id(
        {
            "type": "recorder/get_statistics_metadata",
            "statistic_ids": ["sensor.test"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == [
        {
            "statistic_id": "sensor.test",
            "display_unit_of_measurement": attributes["unit_of_measurement"],
            "has_mean": has_mean,
            "mean_type": mean_type,
            "has_sum": has_sum,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": attributes["unit_of_measurement"],
            "unit_class": unit_class,
        }
    ]

    do_adhoc_statistics(hass, start=now)
    await async_recorder_block_till_done(hass)
    # Remove the state, statistics will now be fetched from the database
    hass.states.async_remove("sensor.test")
    await hass.async_block_till_done()

    await client.send_json_auto_id(
        {
            "type": "recorder/get_statistics_metadata",
            "statistic_ids": ["sensor.test"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == [
        {
            "statistic_id": "sensor.test",
            "display_unit_of_measurement": attributes["unit_of_measurement"],
            "has_mean": has_mean,
            "mean_type": mean_type,
            "has_sum": has_sum,
            "name": None,
            "source": "recorder",
            "statistics_unit_of_measurement": attributes["unit_of_measurement"],
            "unit_class": unit_class,
        }
    ]