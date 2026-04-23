async def test_switches_mqtt_update(
    hass: HomeAssistant,
    mock_fully_kiosk: MagicMock,
    mqtt_mock: MqttMockHAClient,
    init_integration: MockConfigEntry,
) -> None:
    """Test push updates over MQTT."""
    assert has_subscribed(mqtt_mock, "fully/event/onScreensaverStart/abcdef-123456")
    assert has_subscribed(mqtt_mock, "fully/event/onScreensaverStop/abcdef-123456")
    assert has_subscribed(mqtt_mock, "fully/event/screenOff/abcdef-123456")
    assert has_subscribed(mqtt_mock, "fully/event/screenOn/abcdef-123456")

    entity = hass.states.get("switch.amazon_fire_screensaver")
    assert entity
    assert entity.state == "off"

    entity = hass.states.get("switch.amazon_fire_screen")
    assert entity
    assert entity.state == "on"

    async_fire_mqtt_message(
        hass,
        "fully/event/onScreensaverStart/abcdef-123456",
        '{"deviceId": "abcdef-123456","event": "onScreensaverStart"}',
    )
    entity = hass.states.get("switch.amazon_fire_screensaver")
    assert entity.state == "on"

    async_fire_mqtt_message(
        hass,
        "fully/event/onScreensaverStop/abcdef-123456",
        '{"deviceId": "abcdef-123456","event": "onScreensaverStop"}',
    )
    entity = hass.states.get("switch.amazon_fire_screensaver")
    assert entity.state == "off"

    async_fire_mqtt_message(
        hass,
        "fully/event/screenOff/abcdef-123456",
        '{"deviceId": "abcdef-123456","event": "screenOff"}',
    )
    entity = hass.states.get("switch.amazon_fire_screen")
    assert entity.state == "off"

    async_fire_mqtt_message(
        hass,
        "fully/event/screenOn/abcdef-123456",
        '{"deviceId": "abcdef-123456","event": "screenOn"}',
    )
    entity = hass.states.get("switch.amazon_fire_screen")
    assert entity.state == "on"