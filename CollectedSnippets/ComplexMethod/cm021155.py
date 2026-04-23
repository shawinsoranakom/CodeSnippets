async def test_sensors(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    windows: bool,
    single: bool,
    root_folder: str,
) -> None:
    """Test for successfully setting up the Radarr platform."""
    await setup_integration(hass, aioclient_mock, windows=windows, single_return=single)

    state = hass.states.get(f"sensor.mock_title_disk_space_{root_folder}")
    assert state.state == "263.10"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "GB"
    state = hass.states.get("sensor.mock_title_movies")
    assert state.state == "2"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "movies"
    state = hass.states.get("sensor.mock_title_start_time")
    assert state.state == "2020-09-01T23:50:20+00:00"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.TIMESTAMP
    state = hass.states.get("sensor.mock_title_queue")
    assert state.state == "2"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "movies"
    assert state.attributes.get(ATTR_STATE_CLASS) is SensorStateClass.TOTAL