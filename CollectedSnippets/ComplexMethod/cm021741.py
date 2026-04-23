async def test_sensor_imperial_units(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_google_weather_api: AsyncMock,
) -> None:
    """Test states of the sensor with imperial units."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    state = hass.states.get("sensor.home_temperature")
    assert state
    assert state.state == "56.66"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.FAHRENHEIT
    )

    state = hass.states.get("sensor.home_wind_speed")
    assert state
    assert float(state.state) == pytest.approx(4.97097)
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfSpeed.MILES_PER_HOUR

    state = hass.states.get("sensor.home_visibility")
    assert state
    assert float(state.state) == pytest.approx(9.94194)
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfLength.MILES

    state = hass.states.get("sensor.home_atmospheric_pressure")
    assert state
    assert float(state.state) == pytest.approx(30.09578)
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPressure.INHG