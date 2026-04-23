async def test_setup_params(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the initial parameters."""
    await mqtt_mock_entry()

    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 21
    assert state.attributes.get("fan_mode") == "low"
    assert state.attributes.get("swing_mode") == "off"
    assert state.attributes.get("swing_horizontal_mode") == "off"
    assert state.state == "off"
    assert state.attributes.get("min_temp") == DEFAULT_MIN_TEMP
    assert state.attributes.get("max_temp") == DEFAULT_MAX_TEMP
    assert state.attributes.get("min_humidity") == DEFAULT_MIN_HUMIDITY
    assert state.attributes.get("max_humidity") == DEFAULT_MAX_HUMIDITY
    assert (
        state.attributes.get("supported_features")
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.TARGET_HUMIDITY
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.SWING_HORIZONTAL_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )