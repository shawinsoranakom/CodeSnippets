async def test_hmip_weather_sensor_pro(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipWeatherSensorPro."""
    entity_id = "weather.wettersensor_pro"
    entity_name = "Wettersensor - pro"
    device_model = "HmIP-SWO-PR"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "sunny"
    assert ha_state.attributes[ATTR_WEATHER_TEMPERATURE] == 15.4
    assert ha_state.attributes[ATTR_WEATHER_HUMIDITY] == 65
    assert ha_state.attributes[ATTR_WEATHER_WIND_SPEED] == 2.6
    assert ha_state.attributes[ATTR_WEATHER_WIND_BEARING] == 295.0
    assert ha_state.attributes[ATTR_ATTRIBUTION] == "Powered by Homematic IP"

    await async_manipulate_test_data(hass, hmip_device, "actualTemperature", 12.1)
    ha_state = hass.states.get(entity_id)
    assert ha_state.attributes[ATTR_WEATHER_TEMPERATURE] == 12.1