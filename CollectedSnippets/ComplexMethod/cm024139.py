async def test_get_target_temperature_low_high_with_templates(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test getting temperature high/low with templates."""
    await mqtt_mock_entry()

    state = hass.states.get(ENTITY_CLIMATE)

    # Temperature - with valid value
    assert state.attributes.get("target_temp_low") is None
    assert state.attributes.get("target_temp_high") is None

    async_fire_mqtt_message(
        hass, "temperature-state", '{"temp_low": "1031", "temp_high": "1032"}'
    )
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 1031
    assert state.attributes.get("target_temp_high") == 1032

    # Temperature - with invalid value
    async_fire_mqtt_message(
        hass, "temperature-state", '{"temp_low": "INVALID", "temp_high": "INVALID"}'
    )
    state = hass.states.get(ENTITY_CLIMATE)
    # make sure, the invalid value gets logged...
    assert "Could not parse temperature_low_state_template from" in caplog.text
    assert "Could not parse temperature_high_state_template from" in caplog.text
    # ... but the actual value stays unchanged.
    assert state.attributes.get("target_temp_low") == 1031
    assert state.attributes.get("target_temp_high") == 1032

    # Reset the high and low values using a "None" of JSON null value
    async_fire_mqtt_message(
        hass, "temperature-state", '{"temp_low": "None", "temp_high": null}'
    )
    state = hass.states.get(ENTITY_CLIMATE)

    assert state.attributes.get("target_temp_low") is None
    assert state.attributes.get("target_temp_high") is None

    # Test ignoring an empty state works okay
    caplog.clear()
    async_fire_mqtt_message(
        hass, "temperature-state", '{"temp_low": "", "temp_high": "21"}'
    )
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") is None
    assert state.attributes.get("target_temp_high") == 21.0
    async_fire_mqtt_message(
        hass, "temperature-state", '{"temp_low": "18", "temp_high": ""}'
    )
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 18.0
    assert state.attributes.get("target_temp_high") == 21.0
    assert "Could not parse temperature_low_state_template from" not in caplog.text
    assert "Could not parse temperature_high_state_template from" not in caplog.text