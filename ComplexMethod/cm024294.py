async def test_invalid_json_state_message(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test an empty JSON payload."""
    state_topic = "test/state-topic"
    await mqtt_mock_entry()

    async_fire_mqtt_message(
        hass,
        state_topic,
        '{"installed_version":"1.9.0","latest_version":"1.9.0",'
        '"title":"Test Update 1 Title","release_url":"https://example.com/release1",'
        '"release_summary":"Test release summary 1",'
        '"entity_picture": "https://example.com/icon1.png"}',
    )

    await hass.async_block_till_done()

    state = hass.states.get("update.test_update")
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "1.9.0"
    assert state.attributes.get("latest_version") == "1.9.0"
    assert state.attributes.get("release_summary") == "Test release summary 1"
    assert state.attributes.get("release_url") == "https://example.com/release1"
    assert state.attributes.get("title") == "Test Update 1 Title"
    assert state.attributes.get("entity_picture") == "https://example.com/icon1.png"

    # Test update schema validation with invalid value in JSON update
    async_fire_mqtt_message(hass, state_topic, '{"update_percentage":101}')

    await hass.async_block_till_done()
    assert (
        "Schema violation after processing payload '{\"update_percentage\":101}' on "
        "topic 'test/state-topic' for entity 'update.test_update': value must be at "
        "most 100 for dictionary value @ data['update_percentage']" in caplog.text
    )