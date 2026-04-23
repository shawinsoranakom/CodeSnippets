async def test_set_target_temperature_low_high_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setting the low/high target temperature optimistic."""
    await mqtt_mock_entry()

    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 21
    assert state.attributes.get("target_temp_high") == 21
    await common.async_set_temperature(
        hass, target_temp_low=20, target_temp_high=23, entity_id=ENTITY_CLIMATE
    )
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 20
    assert state.attributes.get("target_temp_high") == 23

    async_fire_mqtt_message(hass, "temperature-low-state", "15")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 15
    assert state.attributes.get("target_temp_high") == 23

    async_fire_mqtt_message(hass, "temperature-high-state", "25")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 15
    assert state.attributes.get("target_temp_high") == 25

    async_fire_mqtt_message(hass, "temperature-low-state", "not a number")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 15

    async_fire_mqtt_message(hass, "temperature-high-state", "not a number")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_high") == 25