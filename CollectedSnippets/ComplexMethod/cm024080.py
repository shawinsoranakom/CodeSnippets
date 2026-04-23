async def test_sensors_active_job(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api,
    mock_get_status_printing,
    mock_job_api_printing,
) -> None:
    """Test sensors while active job."""
    with patch(
        "homeassistant.components.prusalink.sensor.utcnow",
        return_value=datetime(2022, 8, 27, 14, 0, 0, tzinfo=UTC),
    ):
        assert await async_setup_component(hass, "prusalink", {})

    state = hass.states.get("sensor.mock_title")
    assert state is not None
    assert state.state == "printing"

    state = hass.states.get("sensor.mock_title_progress")
    assert state is not None
    assert state.state == "37.0"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "%"

    state = hass.states.get("sensor.mock_title_filename")
    assert state is not None
    assert state.state == "TabletStand3.bgcode"

    state = hass.states.get("sensor.mock_title_print_start")
    assert state is not None
    assert state.state == "2022-08-27T01:46:53+00:00"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP

    state = hass.states.get("sensor.mock_title_print_finish")
    assert state is not None
    assert state.state == "2022-08-28T10:17:00+00:00"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP

    state = hass.states.get("sensor.mock_title_hotend_fan")
    assert state is not None
    assert state.state == "5000"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == REVOLUTIONS_PER_MINUTE

    state = hass.states.get("sensor.mock_title_print_fan")
    assert state is not None
    assert state.state == "2500"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == REVOLUTIONS_PER_MINUTE