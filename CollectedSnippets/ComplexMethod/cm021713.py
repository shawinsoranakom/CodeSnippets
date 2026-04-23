async def test_current_weather(hass: HomeAssistant) -> None:
    """Test states of the current weather."""
    with mock_weather_response():
        await init_integration(hass)

    state = hass.states.get("weather.home")
    assert state
    assert state.state == "partlycloudy"
    assert state.attributes[ATTR_WEATHER_HUMIDITY] == 91
    assert state.attributes[ATTR_WEATHER_PRESSURE] == 1009.8
    assert state.attributes[ATTR_WEATHER_TEMPERATURE] == 22.9
    assert state.attributes[ATTR_WEATHER_VISIBILITY] == 20.97
    assert state.attributes[ATTR_WEATHER_WIND_BEARING] == 259
    assert state.attributes[ATTR_WEATHER_WIND_SPEED] == 5.23
    assert state.attributes[ATTR_WEATHER_APPARENT_TEMPERATURE] == 24.9
    assert state.attributes[ATTR_WEATHER_DEW_POINT] == 21.3
    assert state.attributes[ATTR_WEATHER_CLOUD_COVERAGE] == 62
    assert state.attributes[ATTR_WEATHER_WIND_GUST_SPEED] == 10.53
    assert state.attributes[ATTR_WEATHER_UV_INDEX] == 1
    assert state.attributes[ATTR_ATTRIBUTION] == ATTRIBUTION