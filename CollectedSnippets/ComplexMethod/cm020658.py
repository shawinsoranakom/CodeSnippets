async def test_availability_api_error(
    hass: HomeAssistant,
    mock_gios: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Ensure that we mark the entities unavailable correctly when service causes an error."""
    state = hass.states.get("sensor.home_pm2_5")
    assert state
    assert state.state == "4"

    mock_gios.async_update.side_effect = ApiError("Unexpected error")
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.home_pm2_5")
    assert state
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get("sensor.home_pm2_5_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get("sensor.home_air_quality_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    mock_gios.async_update.side_effect = None
    gios_sensors: GiosSensors = mock_gios.async_update.return_value
    old_pm25 = gios_sensors.pm25
    old_aqi = gios_sensors.aqi
    gios_sensors.pm25 = None
    gios_sensors.aqi = None

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # There is no PM2.5 data so the state should be unavailable
    state = hass.states.get("sensor.home_pm2_5")
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Indexes are empty so the state should be unavailable
    state = hass.states.get("sensor.home_air_quality_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Indexes are empty so the state should be unavailable
    state = hass.states.get("sensor.home_pm2_5_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    gios_sensors.pm25 = old_pm25
    gios_sensors.aqi = old_aqi

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.home_pm2_5")
    assert state
    assert state.state == "4"

    state = hass.states.get("sensor.home_pm2_5_index")
    assert state
    assert state.state == "good"

    state = hass.states.get("sensor.home_air_quality_index")
    assert state
    assert state.state == "good"