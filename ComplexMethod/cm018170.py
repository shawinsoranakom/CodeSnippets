async def test_litter_robot_sensor(
    hass: HomeAssistant, mock_account_with_litterrobot_4: MagicMock
) -> None:
    """Tests Litter-Robot sensors."""
    await setup_integration(hass, mock_account_with_litterrobot_4, SENSOR_DOMAIN)

    sensor = hass.states.get(SLEEP_START_TIME_ENTITY_ID)
    assert sensor.state == "2022-09-19T04:00:00+00:00"
    assert sensor.attributes["device_class"] == SensorDeviceClass.TIMESTAMP
    sensor = hass.states.get(SLEEP_END_TIME_ENTITY_ID)
    assert sensor.state == "2022-09-16T07:00:00+00:00"
    assert sensor.attributes["device_class"] == SensorDeviceClass.TIMESTAMP
    sensor = hass.states.get("sensor.test_last_seen")
    assert sensor.state == "2022-09-17T12:06:37+00:00"
    assert sensor.attributes["device_class"] == SensorDeviceClass.TIMESTAMP
    sensor = hass.states.get("sensor.test_status_code")
    assert sensor.state == "rdy"
    assert sensor.attributes["device_class"] == SensorDeviceClass.ENUM
    sensor = hass.states.get("sensor.test_litter_level")
    assert sensor.state == "70.0"
    assert sensor.attributes["unit_of_measurement"] == PERCENTAGE
    sensor = hass.states.get("sensor.test_pet_weight")
    assert sensor.state == "12.0"
    assert sensor.attributes["unit_of_measurement"] == UnitOfMass.POUNDS
    sensor = hass.states.get("sensor.test_total_cycles")
    assert sensor.state == "158"
    assert sensor.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING