async def test_setting_device_tracker_location_via_abbr_reset_message(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the setting of reset via abbreviated names and custom payloads via MQTT."""
    await mqtt_mock_entry()
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        "{ "
        '"name": "test", '
        '"state_topic": "test-topic", '
        '"json_attributes_topic": "attributes-topic", '
        '"pl_rst": "reset" '
        "}",
    )

    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")
    assert state.attributes["source_type"] == "gps"

    assert state.state == STATE_UNKNOWN

    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743

    # test custom reset payload and gps attributes
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":32.87336,"longitude": -117.22743, "gps_accuracy":1.5}',
    )
    async_fire_mqtt_message(hass, "test-topic", "reset")

    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 32.87336
    assert state.attributes["longitude"] == -117.22743
    assert state.attributes["gps_accuracy"] == 1.5
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_HOME

    # Override the GPS state via a direct state update
    async_fire_mqtt_message(hass, "test-topic", "office")
    state = hass.states.get("device_tracker.test")
    assert state.state == "office"

    # Test a GPS attributes update without a reset
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":32.87336,"longitude": -117.22743, "gps_accuracy":1.5}',
    )

    state = hass.states.get("device_tracker.test")
    assert state.state == "office"

    # Reset the manual set location
    # This should calculate the location from GPS attributes
    async_fire_mqtt_message(hass, "test-topic", "reset")
    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 32.87336
    assert state.attributes["longitude"] == -117.22743
    assert state.attributes["gps_accuracy"] == 1.5
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_HOME