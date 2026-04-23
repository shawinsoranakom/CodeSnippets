async def test_set_target_temperature_low_highpessimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setting the low/high target temperature."""
    await mqtt_mock_entry()

    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") is None
    assert state.attributes.get("target_temp_high") is None
    await common.async_set_temperature(
        hass, target_temp_low=20, target_temp_high=23, entity_id=ENTITY_CLIMATE
    )
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") is None
    assert state.attributes.get("target_temp_high") is None

    async_fire_mqtt_message(hass, "temperature-low-state", "1701")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 1701
    assert state.attributes.get("target_temp_high") is None

    async_fire_mqtt_message(hass, "temperature-high-state", "1703")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 1701
    assert state.attributes.get("target_temp_high") == 1703

    async_fire_mqtt_message(hass, "temperature-low-state", "not a number")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 1701

    async_fire_mqtt_message(hass, "temperature-high-state", "not a number")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_high") == 1703