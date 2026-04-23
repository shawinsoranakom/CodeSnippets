async def test_missing_index_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_gios: MagicMock,
    mock_gios_sensors: GiosSensors,
) -> None:
    """Test states of the sensor when API returns invalid indexes."""
    mock_gios_sensors.no2.index = None
    mock_gios_sensors.o3.index = None
    mock_gios_sensors.pm10.index = None
    mock_gios_sensors.pm25.index = None
    mock_gios_sensors.so2.index = None
    mock_gios_sensors.aqi = None

    await setup_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.home_nitrogen_dioxide_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get("sensor.home_ozone_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get("sensor.home_pm10_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get("sensor.home_pm2_5_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get("sensor.home_sulphur_dioxide_index")
    assert state
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get("sensor.home_air_quality_index")
    assert state is None