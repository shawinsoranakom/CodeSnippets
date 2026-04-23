async def test_json_state_message(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test whether it fetches data from a JSON payload."""
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

    async_fire_mqtt_message(
        hass,
        state_topic,
        '{"installed_version":"1.9.0","latest_version":"2.0.0",'
        '"title":"Test Update 2 Title","entity_picture":"https://example.com/icon2.png"}',
    )

    await hass.async_block_till_done()

    state = hass.states.get("update.test_update")
    assert state.state == STATE_ON
    assert state.attributes.get("installed_version") == "1.9.0"
    assert state.attributes.get("latest_version") == "2.0.0"
    assert state.attributes.get("entity_picture") == "https://example.com/icon2.png"
    assert state.attributes.get("in_progress") is False
    assert state.attributes.get("update_percentage") is None

    # Test in_progress status
    async_fire_mqtt_message(hass, state_topic, '{"in_progress":true}')
    await hass.async_block_till_done()

    state = hass.states.get("update.test_update")
    assert state.state == STATE_ON
    assert state.attributes.get("installed_version") == "1.9.0"
    assert state.attributes.get("latest_version") == "2.0.0"
    assert state.attributes.get("entity_picture") == "https://example.com/icon2.png"
    assert state.attributes.get("in_progress") is True
    assert state.attributes.get("update_percentage") is None

    async_fire_mqtt_message(hass, state_topic, '{"in_progress":false}')
    await hass.async_block_till_done()
    state = hass.states.get("update.test_update")
    assert state.attributes.get("in_progress") is False

    # Test update_percentage status
    async_fire_mqtt_message(hass, state_topic, '{"update_percentage":51.75}')
    await hass.async_block_till_done()
    state = hass.states.get("update.test_update")
    assert state.attributes.get("in_progress") is True
    assert state.attributes.get("update_percentage") == 51.75
    assert state.attributes.get("display_precision") == 1

    async_fire_mqtt_message(hass, state_topic, '{"update_percentage":100}')
    await hass.async_block_till_done()
    state = hass.states.get("update.test_update")
    assert state.attributes.get("in_progress") is True
    assert state.attributes.get("update_percentage") == 100

    async_fire_mqtt_message(hass, state_topic, '{"update_percentage":null}')
    await hass.async_block_till_done()
    state = hass.states.get("update.test_update")
    assert state.attributes.get("in_progress") is False
    assert state.attributes.get("update_percentage") is None