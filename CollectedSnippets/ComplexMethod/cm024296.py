async def test_get_with_templates(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test getting various attributes with templates."""
    await mqtt_mock_entry()

    # Operation Mode
    state = hass.states.get(ENTITY_WATER_HEATER)
    async_fire_mqtt_message(hass, "mode-state", '{"attribute": "eco"}')
    state = hass.states.get(ENTITY_WATER_HEATER)
    assert state.state == "eco"

    # Temperature - with valid value
    assert state.attributes.get("temperature") is None
    async_fire_mqtt_message(hass, "temperature-state", '"1031"')
    state = hass.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("temperature") == 1031

    # Temperature - with invalid value
    async_fire_mqtt_message(hass, "temperature-state", '"-INVALID-"')
    state = hass.states.get(ENTITY_WATER_HEATER)
    # make sure, the invalid value gets logged...
    assert "Could not parse temperature_state_template from -INVALID-" in caplog.text
    # ... but the actual value stays unchanged.
    assert state.attributes.get("temperature") == 1031

    # Temperature - with JSON null value
    async_fire_mqtt_message(hass, "temperature-state", "null")
    state = hass.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("temperature") is None

    # Current temperature
    async_fire_mqtt_message(hass, "current-temperature", '"74656"')
    state = hass.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("current_temperature") == 74656
    # Test resetting the current temperature using a JSON null value
    async_fire_mqtt_message(hass, "current-temperature", "null")
    state = hass.states.get(ENTITY_WATER_HEATER)
    assert state.attributes.get("current_temperature") is None