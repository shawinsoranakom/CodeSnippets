async def test_setting_device_tracker_location_via_reset_message(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the automatic inference of zones via MQTT via reset."""
    await mqtt_mock_entry()
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        "{ "
        '"name": "test", '
        '"state_topic": "test-topic", '
        '"json_attributes_topic": "attributes-topic" '
        "}",
    )

    hass.states.async_set(
        "zone.school",
        "zoning",
        {
            "latitude": 30.0,
            "longitude": -100.0,
            "radius": 100,
            "friendly_name": "School",
        },
    )

    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")
    assert state.attributes["source_type"] == "gps"

    assert state.state == STATE_UNKNOWN

    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743

    # test reset and gps attributes
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":32.87336,"longitude": -117.22743, "gps_accuracy":1.5}',
    )
    async_fire_mqtt_message(hass, "test-topic", "None")

    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 32.87336
    assert state.attributes["longitude"] == -117.22743
    assert state.attributes["gps_accuracy"] == 1.5
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_HOME

    # test manual state override
    async_fire_mqtt_message(hass, "test-topic", "Work")

    state = hass.states.get("device_tracker.test")
    assert state.state == "Work"

    # test reset
    async_fire_mqtt_message(hass, "test-topic", "None")

    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_HOME

    # test reset inferring correct school area
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":30.0,"longitude":-100.0,"gps_accuracy":1.5}',
    )

    state = hass.states.get("device_tracker.test")
    assert state.state == "School"