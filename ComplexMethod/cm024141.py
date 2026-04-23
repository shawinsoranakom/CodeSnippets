async def test_set_and_templates(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test setting various attributes with templates."""
    mqtt_mock = await mqtt_mock_entry()

    # Fan Mode
    await common.async_set_fan_mode(hass, "high", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "fan-mode-topic", "fan_mode: high", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "high"

    # Preset Mode
    await common.async_set_preset_mode(hass, PRESET_ECO, ENTITY_CLIMATE)
    assert mqtt_mock.async_publish.call_count == 1
    mqtt_mock.async_publish.assert_any_call(
        "preset-mode-topic", "preset_mode: eco", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == PRESET_ECO

    # Mode
    await common.async_set_hvac_mode(hass, HVACMode.COOL, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_any_call("mode-topic", "mode: cool", 0, False)
    assert mqtt_mock.async_publish.call_count == 1
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"

    await common.async_set_hvac_mode(hass, HVACMode.OFF, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_any_call("mode-topic", "mode: off", 0, False)
    assert mqtt_mock.async_publish.call_count == 1
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.state == "off"

    # Power
    await common.async_turn_on(hass, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_any_call("power-topic", "power: ON", 0, False)
    # Only power command is sent
    # the mode is not updated when power_command_topic is set
    assert mqtt_mock.async_publish.call_count == 1
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.state == "off"

    await common.async_turn_off(hass, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_any_call("power-topic", "power: OFF", 0, False)
    # Only power command is sent
    # the mode is not updated when power_command_topic is set
    assert mqtt_mock.async_publish.call_count == 1
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.state == "off"

    # Swing Horizontal Mode
    await common.async_set_swing_horizontal_mode(hass, "on", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "swing-horizontal-mode-topic", "swing_horizontal_mode: on", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_horizontal_mode") == "on"

    # Swing Mode
    await common.async_set_swing_mode(hass, "on", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "swing-mode-topic", "swing_mode: on", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"

    # Temperature
    await common.async_set_temperature(hass, temperature=35, entity_id=ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "temperature-topic", "temp: 35.0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 35

    # Temperature Low/High
    await common.async_set_temperature(
        hass, target_temp_low=20, target_temp_high=23, entity_id=ENTITY_CLIMATE
    )
    mqtt_mock.async_publish.assert_any_call(
        "temperature-low-topic", "temp_lo: 20.0", 0, False
    )
    mqtt_mock.async_publish.assert_any_call(
        "temperature-high-topic", "temp_hi: 23.0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 20
    assert state.attributes.get("target_temp_high") == 23

    # Humidity
    await common.async_set_humidity(hass, humidity=82, entity_id=ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "humidity-topic", "humidity: 82", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("humidity") == 82