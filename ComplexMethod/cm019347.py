async def test_custom_units(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, config_flow_fixture: None
) -> None:
    """Test custom unit."""
    wind_speed_value = 5
    wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    pressure_value = 110
    pressure_unit = UnitOfPressure.HPA
    temperature_value = 20
    temperature_unit = UnitOfTemperature.CELSIUS
    visibility_value = 11
    visibility_unit = UnitOfLength.KILOMETERS
    precipitation_value = 1.1
    precipitation_unit = UnitOfLength.MILLIMETERS

    set_options = {
        "wind_speed_unit": UnitOfSpeed.MILES_PER_HOUR,
        "precipitation_unit": UnitOfLength.INCHES,
        "pressure_unit": UnitOfPressure.INHG,
        "temperature_unit": UnitOfTemperature.FAHRENHEIT,
        "visibility_unit": UnitOfLength.MILES,
    }

    entry = entity_registry.async_get_or_create("weather", "test", "very_unique")
    entity_registry.async_update_entity_options(entry.entity_id, "weather", set_options)
    await hass.async_block_till_done()

    kwargs = {
        "native_temperature": temperature_value,
        "native_temperature_unit": temperature_unit,
        "native_wind_speed": wind_speed_value,
        "native_wind_speed_unit": wind_speed_unit,
        "native_pressure": pressure_value,
        "native_pressure_unit": pressure_unit,
        "native_visibility": visibility_value,
        "native_visibility_unit": visibility_unit,
        "native_precipitation": precipitation_value,
        "native_precipitation_unit": precipitation_unit,
        "is_daytime": True,
        "unique_id": "very_unique",
    }

    entity0 = await create_entity(hass, MockWeatherTest, None, **kwargs)

    state = hass.states.get(entity0.entity_id)

    expected_wind_speed = round(
        SpeedConverter.convert(
            wind_speed_value, wind_speed_unit, UnitOfSpeed.MILES_PER_HOUR
        ),
        ROUNDING_PRECISION,
    )
    expected_temperature = TemperatureConverter.convert(
        temperature_value, temperature_unit, UnitOfTemperature.FAHRENHEIT
    )
    expected_pressure = round(
        PressureConverter.convert(pressure_value, pressure_unit, UnitOfPressure.INHG),
        ROUNDING_PRECISION,
    )
    expected_visibility = round(
        DistanceConverter.convert(
            visibility_value, visibility_unit, UnitOfLength.MILES
        ),
        ROUNDING_PRECISION,
    )

    assert float(state.attributes[ATTR_WEATHER_WIND_SPEED]) == pytest.approx(
        expected_wind_speed
    )
    assert float(state.attributes[ATTR_WEATHER_TEMPERATURE]) == pytest.approx(
        expected_temperature, rel=0.1
    )
    assert float(state.attributes[ATTR_WEATHER_PRESSURE]) == pytest.approx(
        expected_pressure
    )
    assert float(state.attributes[ATTR_WEATHER_VISIBILITY]) == pytest.approx(
        expected_visibility
    )

    assert (
        state.attributes[ATTR_WEATHER_PRECIPITATION_UNIT]
        == set_options["precipitation_unit"]
    )
    assert state.attributes[ATTR_WEATHER_PRESSURE_UNIT] == set_options["pressure_unit"]
    assert (
        state.attributes[ATTR_WEATHER_TEMPERATURE_UNIT]
        == set_options["temperature_unit"]
    )
    assert (
        state.attributes[ATTR_WEATHER_VISIBILITY_UNIT] == set_options["visibility_unit"]
    )
    assert (
        state.attributes[ATTR_WEATHER_WIND_SPEED_UNIT] == set_options["wind_speed_unit"]
    )