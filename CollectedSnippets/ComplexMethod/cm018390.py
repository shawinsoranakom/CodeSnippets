async def test_aemet_weather(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test states of the weather."""

    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    await async_init_integration(hass)

    state = hass.states.get("weather.aemet")
    assert state
    assert state.state == ATTR_CONDITION_SNOWY
    assert state.attributes[ATTR_ATTRIBUTION] == ATTRIBUTION
    assert state.attributes[ATTR_WEATHER_HUMIDITY] == 99.0
    assert state.attributes[ATTR_WEATHER_PRESSURE] == 1004.4  # 100440.0 Pa -> hPa
    assert state.attributes[ATTR_WEATHER_TEMPERATURE] == -0.7
    assert state.attributes[ATTR_WEATHER_WIND_BEARING] == 122.0
    assert state.attributes[ATTR_WEATHER_WIND_GUST_SPEED] == 12.2
    assert state.attributes[ATTR_WEATHER_WIND_SPEED] == 3.2

    state = hass.states.get("weather.aemet_hourly")
    assert state is None