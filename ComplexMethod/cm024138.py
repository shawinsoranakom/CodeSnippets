async def test_set_preset_mode_pessimistic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test setting of the preset mode."""
    await mqtt_mock_entry()

    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"

    async_fire_mqtt_message(hass, "preset-mode-state", "away")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "away"

    async_fire_mqtt_message(hass, "preset-mode-state", "eco")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "eco"

    async_fire_mqtt_message(hass, "preset-mode-state", "none")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"

    async_fire_mqtt_message(hass, "preset-mode-state", "comfort")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "comfort"

    async_fire_mqtt_message(hass, "preset-mode-state", "")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "comfort"

    async_fire_mqtt_message(hass, "preset-mode-state", "None")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"

    async_fire_mqtt_message(hass, "preset-mode-state", "home")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "home"

    async_fire_mqtt_message(hass, "preset-mode-state", "nonsense")
    assert (
        "'nonsense' received on topic preset-mode-state."
        " 'nonsense' is not a valid preset mode" in caplog.text
    )

    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "home"