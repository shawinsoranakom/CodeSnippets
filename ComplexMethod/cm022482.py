async def test_sensorstate(
    hass: HomeAssistant, value: Any, published: Any, aqi: Any
) -> None:
    """Test SensorState trait support for sensor domain."""
    sensor_types = {
        sensor.SensorDeviceClass.AQI: ("AirQuality", "AQI"),
        sensor.SensorDeviceClass.CO: ("CarbonMonoxideLevel", "PARTS_PER_MILLION"),
        sensor.SensorDeviceClass.CO2: ("CarbonDioxideLevel", "PARTS_PER_MILLION"),
        sensor.SensorDeviceClass.PM25: ("PM2.5", "MICROGRAMS_PER_CUBIC_METER"),
        sensor.SensorDeviceClass.PM10: ("PM10", "MICROGRAMS_PER_CUBIC_METER"),
        sensor.SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS: (
            "VolatileOrganicCompounds",
            "PARTS_PER_MILLION",
        ),
    }

    for sensor_type, item in sensor_types.items():
        assert helpers.get_google_type(sensor.DOMAIN, None) is not None
        assert trait.SensorStateTrait.supported(sensor.DOMAIN, None, sensor_type, None)

        trt = trait.SensorStateTrait(
            hass,
            State(
                "sensor.test",
                value,
                {
                    "device_class": sensor_type,
                },
            ),
            BASIC_CONFIG,
        )

        name = item[0]
        unit = item[1]

        if sensor_type == sensor.SensorDeviceClass.AQI:
            assert trt.sync_attributes() == {
                "sensorStatesSupported": [
                    {
                        "name": name,
                        "numericCapabilities": {"rawValueUnit": unit},
                        "descriptiveCapabilities": {
                            "availableStates": [
                                "healthy",
                                "moderate",
                                "unhealthy for sensitive groups",
                                "unhealthy",
                                "very unhealthy",
                                "hazardous",
                                "unknown",
                            ],
                        },
                    }
                ]
            }
        else:
            assert trt.sync_attributes() == {
                "sensorStatesSupported": [
                    {
                        "name": name,
                        "numericCapabilities": {"rawValueUnit": unit},
                    }
                ]
            }

        if sensor_type == sensor.SensorDeviceClass.AQI:
            assert trt.query_attributes() == {
                "currentSensorStateData": [
                    {
                        "name": name,
                        "currentSensorState": aqi,
                        "rawValue": published,
                    },
                ]
            }
        else:
            assert trt.query_attributes() == {
                "currentSensorStateData": [{"name": name, "rawValue": published}]
            }

    assert helpers.get_google_type(sensor.DOMAIN, None) is not None
    assert (
        trait.SensorStateTrait.supported(
            sensor.DOMAIN, None, sensor.SensorDeviceClass.MONETARY, None
        )
        is False
    )