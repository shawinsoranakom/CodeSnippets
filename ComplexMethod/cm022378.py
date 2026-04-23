async def test_weather(hass: HomeAssistant, mock_weather) -> None:
    """Test states of the weather."""

    await init_integration(hass)
    assert len(hass.states.async_entity_ids("weather")) == 1
    entity_id = hass.states.async_entity_ids("weather")[0]

    state = hass.states.get(entity_id)
    assert state
    assert state.state == ATTR_CONDITION_CLOUDY
    assert state.attributes[ATTR_WEATHER_TEMPERATURE] == 15
    assert state.attributes[ATTR_WEATHER_PRESSURE] == 100
    assert state.attributes[ATTR_WEATHER_HUMIDITY] == 50
    assert state.attributes[ATTR_WEATHER_WIND_SPEED] == 10
    assert state.attributes[ATTR_WEATHER_WIND_BEARING] == 90
    assert state.attributes[ATTR_WEATHER_DEW_POINT] == 12.1
    assert state.attributes[ATTR_WEATHER_UV_INDEX] == 1.1