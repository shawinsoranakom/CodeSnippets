async def test_sensors_no_job(hass: HomeAssistant, mock_config_entry, mock_api) -> None:
    """Test sensors while no job active."""
    assert await async_setup_component(hass, "prusalink", {})

    state = hass.states.get("sensor.mock_title")
    assert state is not None
    assert state.state == "idle"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM
    assert state.attributes[ATTR_OPTIONS] == [
        "idle",
        "busy",
        "printing",
        "paused",
        "finished",
        "stopped",
        "error",
        "attention",
        "ready",
    ]

    state = hass.states.get("sensor.mock_title_heatbed_temperature")
    assert state is not None
    assert state.state == "41.9"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.mock_title_nozzle_temperature")
    assert state is not None
    assert state.state == "47.8"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.mock_title_heatbed_target_temperature")
    assert state is not None
    assert state.state == "60.5"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.mock_title_nozzle_target_temperature")
    assert state is not None
    assert state.state == "210.1"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.mock_title_z_height")
    assert state is not None
    assert state.state == "1.8"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfLength.MILLIMETERS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.DISTANCE
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.mock_title_print_speed")
    assert state is not None
    assert state.state == "100"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE

    state = hass.states.get("sensor.mock_title_material")
    assert state is not None
    assert state.state == "PLA"

    state = hass.states.get("sensor.mock_title_nozzle_diameter")
    assert state is not None
    assert state.state == "0.4"

    state = hass.states.get("sensor.mock_title_print_flow")
    assert state is not None
    assert state.state == "100"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE

    state = hass.states.get("sensor.mock_title_progress")
    assert state is not None
    assert state.state == "unavailable"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "%"

    state = hass.states.get("sensor.mock_title_filename")
    assert state is not None
    assert state.state == "unavailable"

    state = hass.states.get("sensor.mock_title_print_start")
    assert state is not None
    assert state.state == "unavailable"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP

    state = hass.states.get("sensor.mock_title_print_finish")
    assert state is not None
    assert state.state == "unavailable"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP

    state = hass.states.get("sensor.mock_title_hotend_fan")
    assert state is not None
    assert state.state == "100"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == REVOLUTIONS_PER_MINUTE

    state = hass.states.get("sensor.mock_title_print_fan")
    assert state is not None
    assert state.state == "75"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == REVOLUTIONS_PER_MINUTE