def test_unit_conversion_factory_allow_none_with_none() -> None:
    """Test test_unit_conversion_factory_allow_none with None."""
    assert (
        SpeedConverter.converter_factory_allow_none(
            UnitOfSpeed.FEET_PER_SECOND, UnitOfSpeed.FEET_PER_SECOND
        )(1)
        == 1
    )
    assert (
        SpeedConverter.converter_factory_allow_none(
            UnitOfSpeed.FEET_PER_SECOND, UnitOfSpeed.FEET_PER_SECOND
        )(None)
        is None
    )
    assert (
        TemperatureConverter.converter_factory_allow_none(
            UnitOfTemperature.CELSIUS, UnitOfTemperature.CELSIUS
        )(1)
        == 1
    )
    assert (
        TemperatureConverter.converter_factory_allow_none(
            UnitOfTemperature.CELSIUS, UnitOfTemperature.CELSIUS
        )(None)
        is None
    )
    assert (
        TemperatureDeltaConverter.converter_factory_allow_none(
            UnitOfTemperature.CELSIUS, UnitOfTemperature.CELSIUS
        )(1)
        == 1
    )
    assert (
        TemperatureDeltaConverter.converter_factory_allow_none(
            UnitOfTemperature.CELSIUS, UnitOfTemperature.CELSIUS
        )(None)
        is None
    )
    assert (
        EnergyDistanceConverter.converter_factory_allow_none(
            UnitOfEnergyDistance.MILES_PER_KILO_WATT_HOUR,
            UnitOfEnergyDistance.KILO_WATT_HOUR_PER_100_KM,
        )(0)
        is None
    )
    assert (
        EnergyDistanceConverter.converter_factory_allow_none(
            UnitOfEnergyDistance.KILO_WATT_HOUR_PER_100_KM,
            UnitOfEnergyDistance.WATT_HOUR_PER_KM,
        )(0)
        == 0
    )
    assert (
        EnergyDistanceConverter.converter_factory_allow_none(
            UnitOfEnergyDistance.KM_PER_KILO_WATT_HOUR,
            UnitOfEnergyDistance.MILES_PER_KILO_WATT_HOUR,
        )(0.0)
        == 0.0
    )
    assert (
        EnergyDistanceConverter.converter_factory_allow_none(
            UnitOfEnergyDistance.MILES_PER_KILO_WATT_HOUR,
            UnitOfEnergyDistance.KM_PER_KILO_WATT_HOUR,
        )(0)
        == 0.0
    )