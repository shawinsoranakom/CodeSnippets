async def test_attr(hass: HomeAssistant) -> None:
    """Test the _attr attributes."""

    weather = MockWeatherEntity()
    weather.hass = hass

    assert weather.condition == ATTR_CONDITION_SUNNY
    assert weather.native_precipitation_unit == UnitOfLength.MILLIMETERS
    assert weather._precipitation_unit == UnitOfLength.MILLIMETERS
    assert weather.native_pressure == 10
    assert weather.native_pressure_unit == UnitOfPressure.HPA
    assert weather._pressure_unit == UnitOfPressure.HPA
    assert weather.native_temperature == 20
    assert weather.native_temperature_unit == UnitOfTemperature.CELSIUS
    assert weather._temperature_unit == UnitOfTemperature.CELSIUS
    assert weather.native_visibility == 30
    assert weather.native_visibility_unit == UnitOfLength.KILOMETERS
    assert weather._visibility_unit == UnitOfLength.KILOMETERS
    assert weather.native_wind_speed == 3
    assert weather.native_wind_speed_unit == UnitOfSpeed.METERS_PER_SECOND
    assert weather._wind_speed_unit == UnitOfSpeed.KILOMETERS_PER_HOUR