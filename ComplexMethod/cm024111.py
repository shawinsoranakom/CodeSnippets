async def test_sensor_error(
    hass: HomeAssistant,
    mock_egauge_client: MagicMock,
    freezer: FrozenDateTimeFactory,
    exception: Exception,
) -> None:
    """Test errors that occur after setup are handled."""

    # Trigger exception on next update
    mock_egauge_client.get_current_measurements.side_effect = exception

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

    # Clear exception
    mock_egauge_client.get_current_measurements.side_effect = None

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