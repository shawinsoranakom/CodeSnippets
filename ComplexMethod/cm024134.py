async def test_set_swing_pessimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setting swing mode in pessimistic mode."""
    await mqtt_mock_entry()

    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") is None
    assert state.attributes.get("swing_horizontal_mode") is None

    await common.async_set_swing_mode(hass, "on", ENTITY_CLIMATE)
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") is None

    await common.async_set_swing_horizontal_mode(hass, "on", ENTITY_CLIMATE)
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_horizontal_mode") is None

    async_fire_mqtt_message(hass, "swing-state", "on")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"

    async_fire_mqtt_message(hass, "swing-horizontal-state", "on")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_horizontal_mode") == "on"

    async_fire_mqtt_message(hass, "swing-state", "bogus state")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"

    async_fire_mqtt_message(hass, "swing-horizontal-state", "bogus state")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_horizontal_mode") == "on"