async def test_air_quality_description_for_aqi(hass: HomeAssistant) -> None:
    """Test air quality description for a given AQI value."""
    trt = trait.SensorStateTrait(
        hass,
        State(
            "sensor.test",
            100.0,
            {
                "device_class": sensor.SensorDeviceClass.AQI,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt._air_quality_description_for_aqi(0) == "healthy"
    assert trt._air_quality_description_for_aqi(75) == "moderate"
    assert (
        trt._air_quality_description_for_aqi(125.0) == "unhealthy for sensitive groups"
    )
    assert trt._air_quality_description_for_aqi(175) == "unhealthy"
    assert trt._air_quality_description_for_aqi(250) == "very unhealthy"
    assert trt._air_quality_description_for_aqi(350) == "hazardous"
    assert trt._air_quality_description_for_aqi(-1) == "unknown"