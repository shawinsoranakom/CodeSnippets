def test_properties() -> None:
    """Test the unit properties are returned as expected."""
    assert METRIC_SYSTEM.length_unit == UnitOfLength.KILOMETERS
    assert METRIC_SYSTEM.wind_speed_unit == UnitOfSpeed.METERS_PER_SECOND
    assert METRIC_SYSTEM.temperature_unit == UnitOfTemperature.CELSIUS
    assert METRIC_SYSTEM.mass_unit == UnitOfMass.GRAMS
    assert METRIC_SYSTEM.volume_unit == UnitOfVolume.LITERS
    assert METRIC_SYSTEM.pressure_unit == UnitOfPressure.PA
    assert METRIC_SYSTEM.accumulated_precipitation_unit == UnitOfLength.MILLIMETERS
    assert METRIC_SYSTEM.area_unit == UnitOfArea.SQUARE_METERS