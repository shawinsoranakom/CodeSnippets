async def test_v4_weather_legacy_entities(hass: HomeAssistant) -> None:
    """Test v4 weather data."""
    weather_state = await _setup_legacy(hass, API_V4_ENTRY_DATA)
    assert weather_state.state == ATTR_CONDITION_SUNNY
    assert weather_state.attributes[ATTR_ATTRIBUTION] == ATTRIBUTION
    assert weather_state.attributes[ATTR_FRIENDLY_NAME] == "Tomorrow.io Daily"
    assert weather_state.attributes[ATTR_WEATHER_HUMIDITY] == 23
    assert weather_state.attributes[ATTR_WEATHER_OZONE] == 46.53
    assert weather_state.attributes[ATTR_WEATHER_PRECIPITATION_UNIT] == "mm"
    assert weather_state.attributes[ATTR_WEATHER_PRESSURE] == 30.35
    assert weather_state.attributes[ATTR_WEATHER_PRESSURE_UNIT] == "hPa"
    assert weather_state.attributes[ATTR_WEATHER_TEMPERATURE] == 44.1
    assert weather_state.attributes[ATTR_WEATHER_TEMPERATURE_UNIT] == "°C"
    assert weather_state.attributes[ATTR_WEATHER_VISIBILITY] == 8.15
    assert weather_state.attributes[ATTR_WEATHER_VISIBILITY_UNIT] == "km"
    assert weather_state.attributes[ATTR_WEATHER_WIND_BEARING] == 315.14
    assert weather_state.attributes[ATTR_WEATHER_WIND_SPEED] == 33.59  # 9.33 m/s ->km/h
    assert weather_state.attributes[ATTR_WEATHER_WIND_SPEED_UNIT] == "km/h"