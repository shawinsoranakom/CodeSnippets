async def test_sensor_imperial_units(
    hass: HomeAssistant, mock_accuweather_client: AsyncMock
) -> None:
    """Test states of the sensor without forecast."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    await init_integration(hass)

    state = hass.states.get("sensor.home_cloud_ceiling")
    assert state
    assert state.state == "10498.687664042"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfLength.FEET

    state = hass.states.get("sensor.home_wind_speed")
    assert state
    assert float(state.state) == pytest.approx(9.00988)
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfSpeed.MILES_PER_HOUR

    state = hass.states.get("sensor.home_realfeel_temperature")
    assert state
    assert state.state == "77.18"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.FAHRENHEIT
    )