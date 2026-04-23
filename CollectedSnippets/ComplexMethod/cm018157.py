async def test_sensor_update(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test if the sensors get updated when there is new data."""
    client, _, _ = await init_integration(
        hass,
        config_entry,
        "sensor",
        status=charge_point_status | charge_point_status_timestamps,
        grid=grid,
    )

    await client.receiver(
        {
            "object": "CH_STATUS",
            "data": {
                "evse_id": "101",
                "avg_voltage": 20,
                "start_datetime": None,
                "actual_kwh": None,
            },
        }
    )
    await hass.async_block_till_done()

    await client.receiver(
        {
            "object": "GRID_STATUS",
            "data": {"grid_avg_current": 20},
        }
    )
    await hass.async_block_till_done()

    # test data updated
    state = hass.states.get("sensor.101_average_voltage")
    assert state is not None
    assert state.state == str(20)

    # grid
    state = hass.states.get("sensor.average_grid_current")
    assert state
    assert state.state == str(20)

    # test unavailable
    state = hass.states.get("sensor.101_energy_usage")
    assert state
    assert state.state == "unavailable"

    # test if timestamp keeps old value
    state = hass.states.get("sensor.101_started_on")
    assert state
    assert (
        datetime.strptime(state.state, "%Y-%m-%dT%H:%M:%S%z")
        == charge_point_status_timestamps["start_datetime"]
    )

    # test if older timestamp is ignored
    await client.receiver(
        {
            "object": "CH_STATUS",
            "data": {
                "evse_id": "101",
                "start_datetime": datetime.strptime(
                    "20211118 14:11:23+08:00", "%Y%m%d %H:%M:%S%z"
                ),
            },
        }
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.101_started_on")
    assert state
    assert (
        datetime.strptime(state.state, "%Y-%m-%dT%H:%M:%S%z")
        == charge_point_status_timestamps["start_datetime"]
    )