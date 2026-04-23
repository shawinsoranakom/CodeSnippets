async def test_attributes(hass: HomeAssistant, weather_only) -> None:
    """Test weather attributes."""
    assert await async_setup_component(
        hass, weather.DOMAIN, {"weather": {"platform": "demo"}}
    )
    hass.config.units = METRIC_SYSTEM
    await hass.async_block_till_done()

    state = hass.states.get("weather.demo_weather_south")
    assert state is not None

    assert state.state == "sunny"

    data = state.attributes
    assert data.get(ATTR_WEATHER_TEMPERATURE) == 21.6
    assert data.get(ATTR_WEATHER_HUMIDITY) == 92
    assert data.get(ATTR_WEATHER_PRESSURE) == 1099
    assert data.get(ATTR_WEATHER_WIND_SPEED) == 1.8  # 0.5 m/s -> km/h
    assert data.get(ATTR_WEATHER_WIND_BEARING) is None
    assert data.get(ATTR_WEATHER_OZONE) is None
    assert data.get(ATTR_ATTRIBUTION) == "Powered by Home Assistant"