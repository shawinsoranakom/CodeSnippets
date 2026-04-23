async def test_feeder_robot_sensor(
    hass: HomeAssistant, mock_account_with_feederrobot: MagicMock
) -> None:
    """Tests Feeder-Robot sensors."""
    await setup_integration(hass, mock_account_with_feederrobot, SENSOR_DOMAIN)
    sensor = hass.states.get("sensor.test_food_level")
    assert sensor.state == "10"
    assert sensor.attributes["unit_of_measurement"] == PERCENTAGE

    sensor = hass.states.get("sensor.test_last_feeding")
    assert sensor.state == "2022-09-08T18:00:00+00:00"
    assert sensor.attributes["device_class"] == SensorDeviceClass.TIMESTAMP

    sensor = hass.states.get("sensor.test_next_feeding")
    assert sensor.state == "2022-09-09T12:30:00+00:00"
    assert sensor.attributes["device_class"] == SensorDeviceClass.TIMESTAMP

    sensor = hass.states.get("sensor.test_food_dispensed_today")
    assert sensor.state == "0.375"
    assert sensor.attributes["last_reset"] == "2022-09-08T00:00:00-07:00"
    assert sensor.attributes["state_class"] == SensorStateClass.TOTAL
    assert sensor.attributes["unit_of_measurement"] == "cups"