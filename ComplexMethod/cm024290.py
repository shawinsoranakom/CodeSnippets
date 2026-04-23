async def test_run_update_setup_float(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test that it fetches the given payload when the version is parsable as a number."""
    installed_version_topic = "test/installed-version"
    latest_version_topic = "test/latest-version"
    await mqtt_mock_entry()

    async_fire_mqtt_message(hass, installed_version_topic, "1.9")
    async_fire_mqtt_message(hass, latest_version_topic, "1.9")

    await hass.async_block_till_done()

    state = hass.states.get("update.test_update")
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "1.9"
    assert state.attributes.get("latest_version") == "1.9"
    assert state.attributes.get("release_summary") == "Test release summary"
    assert state.attributes.get("release_url") == "https://example.com/release"
    assert state.attributes.get("title") == "Test Update Title"
    assert state.attributes.get("entity_picture") == "https://example.com/icon.png"

    async_fire_mqtt_message(hass, latest_version_topic, "2.0")

    await hass.async_block_till_done()

    state = hass.states.get("update.test_update")
    assert state.state == STATE_ON
    assert state.attributes.get("installed_version") == "1.9"
    assert state.attributes.get("latest_version") == "2.0"