async def test_sensor_attributes(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate the sensor attributes."""

    config = {
        "rflink": {"port": "/dev/ttyABC0"},
        DOMAIN: {
            "platform": "rflink",
            "devices": {
                "my_meter_device_unique_id": {
                    "name": "meter_device",
                    "sensor_type": "meter_value",
                },
                "my_rain_device_unique_id": {
                    "name": "rain_device",
                    "sensor_type": "total_rain",
                },
                "my_humidity_device_unique_id": {
                    "name": "humidity_device",
                    "sensor_type": "humidity",
                },
                "my_temperature_device_unique_id": {
                    "name": "temperature_device",
                    "sensor_type": "temperature",
                },
                "another_temperature_device_unique_id": {
                    "name": "fahrenheit_device",
                    "sensor_type": "temperature",
                    "unit_of_measurement": "F",
                },
            },
        },
    }

    # setup mocking rflink module
    _event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN, monkeypatch)

    # test sensor loaded from config
    meter_state = hass.states.get("sensor.meter_device")
    assert meter_state
    assert "device_class" not in meter_state.attributes
    assert "state_class" not in meter_state.attributes
    assert "unit_of_measurement" not in meter_state.attributes

    rain_state = hass.states.get("sensor.rain_device")
    assert rain_state
    assert rain_state.attributes["device_class"] == SensorDeviceClass.PRECIPITATION
    assert rain_state.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING
    assert (
        rain_state.attributes["unit_of_measurement"]
        == UnitOfPrecipitationDepth.MILLIMETERS
    )

    humidity_state = hass.states.get("sensor.humidity_device")
    assert humidity_state
    assert humidity_state.attributes["device_class"] == SensorDeviceClass.HUMIDITY
    assert humidity_state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert humidity_state.attributes["unit_of_measurement"] == PERCENTAGE

    temperature_state = hass.states.get("sensor.temperature_device")
    assert temperature_state
    assert temperature_state.attributes["device_class"] == SensorDeviceClass.TEMPERATURE
    assert temperature_state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert (
        temperature_state.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS
    )

    fahrenheit_state = hass.states.get("sensor.fahrenheit_device")
    assert fahrenheit_state
    assert fahrenheit_state.attributes["device_class"] == SensorDeviceClass.TEMPERATURE
    assert fahrenheit_state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert fahrenheit_state.attributes["unit_of_measurement"] == "F"