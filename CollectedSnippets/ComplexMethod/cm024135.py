async def test_set_swing_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setting swing mode in optimistic mode."""
    await mqtt_mock_entry()

    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "off"
    assert state.attributes.get("swing_horizontal_mode") == "off"

    await common.async_set_swing_mode(hass, "on", ENTITY_CLIMATE)
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"

    await common.async_set_swing_horizontal_mode(hass, "on", ENTITY_CLIMATE)
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_horizontal_mode") == "on"

    async_fire_mqtt_message(hass, "swing-state", "off")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "off"

    async_fire_mqtt_message(hass, "swing-horizontal-state", "off")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_horizontal_mode") == "off"

    async_fire_mqtt_message(hass, "swing-state", "bogus state")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "off"

    async_fire_mqtt_message(hass, "swing-horizontal-state", "bogus state")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_horizontal_mode") == "off"