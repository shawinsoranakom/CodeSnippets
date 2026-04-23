async def test_hmip_home_weather(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipHomeWeather."""
    entity_id = "weather.weather_1010_wien_osterreich"
    entity_name = "Weather 1010  Wien, Österreich"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap()

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )
    assert hmip_device
    assert ha_state.state == "partlycloudy"
    assert ha_state.attributes[ATTR_WEATHER_TEMPERATURE] == 16.6
    assert ha_state.attributes[ATTR_WEATHER_HUMIDITY] == 54
    assert ha_state.attributes[ATTR_WEATHER_WIND_SPEED] == 8.6
    assert ha_state.attributes[ATTR_WEATHER_WIND_BEARING] == 294
    assert ha_state.attributes[ATTR_ATTRIBUTION] == "Powered by Homematic IP"

    await async_manipulate_test_data(
        hass, mock_hap.home.weather, "temperature", 28.3, fire_device=mock_hap.home
    )

    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_WEATHER_TEMPERATURE] == 28.3