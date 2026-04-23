async def test_value_template(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test that it fetches the given payload with a template."""
    installed_version_topic = "test/installed-version"
    latest_version_topic = "test/latest-version"
    await mqtt_mock_entry()

    async_fire_mqtt_message(hass, installed_version_topic, '{"installed":"1.9.0"}')
    async_fire_mqtt_message(hass, latest_version_topic, '{"latest":"1.9.0"}')

    await hass.async_block_till_done()

    state = hass.states.get("update.test_update")
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "1.9.0"
    assert state.attributes.get("latest_version") == "1.9.0"
    assert state.attributes.get("entity_picture") is None

    async_fire_mqtt_message(hass, latest_version_topic, '{"latest":"2.0.0"}')

    await hass.async_block_till_done()

    state = hass.states.get("update.test_update")
    assert state.state == STATE_ON
    assert state.attributes.get("installed_version") == "1.9.0"
    assert state.attributes.get("latest_version") == "2.0.0"