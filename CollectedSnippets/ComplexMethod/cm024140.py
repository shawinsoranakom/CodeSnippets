async def test_get_with_templates(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test getting various attributes with templates."""
    await mqtt_mock_entry()

    # Operation Mode
    state = hass.states.get(ENTITY_CLIMATE)
    async_fire_mqtt_message(hass, "mode-state", '"cool"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"

    # Fan Mode
    assert state.attributes.get("fan_mode") is None
    async_fire_mqtt_message(hass, "fan-state", '"high"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "high"

    # Swing Mode
    assert state.attributes.get("swing_mode") is None
    async_fire_mqtt_message(hass, "swing-state", '"on"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"

    # Swing Horizontal Mode
    assert state.attributes.get("swing_horizontal_mode") is None
    async_fire_mqtt_message(hass, "swing-horizontal-state", '"on"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_horizontal_mode") == "on"

    # Temperature - with valid value
    assert state.attributes.get("temperature") is None
    async_fire_mqtt_message(hass, "temperature-state", '"1031"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 1031

    # Temperature - with invalid value
    async_fire_mqtt_message(hass, "temperature-state", '"-INVALID-"')
    state = hass.states.get(ENTITY_CLIMATE)
    # make sure, the invalid value gets logged...
    assert "Could not parse temperature_state_template from -INVALID-" in caplog.text
    # ... but the actual value stays unchanged.
    assert state.attributes.get("temperature") == 1031

    # Temperature - with JSON null value
    async_fire_mqtt_message(hass, "temperature-state", "null")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") is None

    # Humidity - with valid value
    assert state.attributes.get("humidity") is None
    async_fire_mqtt_message(hass, "humidity-state", '"82"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("humidity") == 82

    # Humidity - with invalid value
    async_fire_mqtt_message(hass, "humidity-state", '"-INVALID-"')
    state = hass.states.get(ENTITY_CLIMATE)
    # make sure, the invalid value gets logged...
    assert (
        "Could not parse target_humidity_state_template from -INVALID-" in caplog.text
    )
    # ... but the actual value stays unchanged.
    assert state.attributes.get("humidity") == 82

    # reset the humidity
    async_fire_mqtt_message(hass, "humidity-state", "null")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("humidity") is None

    # Preset Mode
    assert state.attributes.get("preset_mode") == "none"
    async_fire_mqtt_message(hass, "current-preset-mode", '{"attribute": "eco"}')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "eco"
    # Test with an empty json
    async_fire_mqtt_message(
        hass, "current-preset-mode", '{"other_attribute": "some_value"}'
    )
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "eco"

    # Current temperature
    async_fire_mqtt_message(hass, "current-temperature", '"74656"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("current_temperature") == 74656
    # Test resetting the current temperature using a JSON null value
    async_fire_mqtt_message(hass, "current-temperature", "null")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("current_temperature") is None

    # Current humidity
    async_fire_mqtt_message(hass, "current-humidity", '"35"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("current_humidity") == 35
    async_fire_mqtt_message(hass, "current-humidity", "null")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("current_humidity") is None

    # Action
    async_fire_mqtt_message(hass, "action", '"cooling"')
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("hvac_action") == "cooling"

    # Test ignoring empty values
    async_fire_mqtt_message(hass, "action", "")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("hvac_action") == "cooling"

    # Test resetting with null values
    async_fire_mqtt_message(hass, "action", "null")
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("hvac_action") is None