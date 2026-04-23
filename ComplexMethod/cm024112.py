async def test_register_removed(
    hass: HomeAssistant,
    mock_egauge_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test case where a register is removed on the eGauge device."""

    # Remove "Grid" register
    original_measurements = await mock_egauge_client.get_current_measurements()
    original_counters = await mock_egauge_client.get_current_counters()
    new_measurements = {k: v for k, v in original_measurements.items() if k != "Grid"}
    new_counters = {k: v for k, v in original_counters.items() if k != "Grid"}
    mock_egauge_client.get_current_measurements.return_value = new_measurements
    mock_egauge_client.get_current_counters.return_value = new_counters

    # Trigger update
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Test Grid power sensor
    state = hass.states.get("sensor.egauge_home_grid_power")
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Test Grid energy sensor
    state = hass.states.get("sensor.egauge_home_grid_energy")
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Test that other sensors still work
    state = hass.states.get("sensor.egauge_home_solar_power")
    assert state
    assert state.state == "-2500.0"

    state = hass.states.get("sensor.egauge_home_solar_energy")
    assert state
    assert state.state == "87.5"

    # Restore "Grid" register
    mock_egauge_client.get_current_measurements.return_value = original_measurements
    mock_egauge_client.get_current_counters.return_value = original_counters

    # Trigger update
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Test Grid power sensor is available
    state = hass.states.get("sensor.egauge_home_grid_power")
    assert state
    assert state.state == "1500.0"

    # Test Grid energy sensor is available
    state = hass.states.get("sensor.egauge_home_grid_energy")
    assert state
    assert state.state == "125.0"