async def test_setting_device_tracker_location_via_lat_lon_message(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the setting of the latitude and longitude via MQTT without state topic."""
    await mqtt_mock_entry()
    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "name": "test", "json_attributes_topic": "attributes-topic"}',
    )
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.test")
    assert state.attributes["source_type"] == "gps"

    assert state.state == STATE_UNKNOWN

    hass.config.latitude = 32.87336
    hass.config.longitude = -117.22743

    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":32.87336,"longitude": -117.22743, "gps_accuracy":1.5, "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 32.87336
    assert state.attributes["longitude"] == -117.22743
    assert state.attributes["gps_accuracy"] == 1.5
    # assert source_type is overridden by discovery
    assert state.attributes["source_type"] == "router"
    assert state.state == STATE_HOME

    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude":50.1,"longitude": -2.1}',
    )
    state = hass.states.get("device_tracker.test")
    assert state.attributes["latitude"] == 50.1
    assert state.attributes["longitude"] == -2.1
    assert state.attributes["gps_accuracy"] == 0
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_NOT_HOME

    # incomplete coordinates results in unknown state
    async_fire_mqtt_message(hass, "attributes-topic", '{"longitude": -117.22743}')
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "attributes-topic", '{"latitude":32.87336}')
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_UNKNOWN

    # invalid coordinates results in unknown state
    async_fire_mqtt_message(
        hass, "attributes-topic", '{"longitude": -117.22743, "latitude":null}'
    )
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.attributes["source_type"] == "gps"
    assert state.state == STATE_UNKNOWN

    # Test number validation
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude": "32.87336","longitude": "-117.22743", "gps_accuracy": "1.5", "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert "gps_accuracy" not in state.attributes
    # assert source_type is overridden by discovery
    assert state.attributes["source_type"] == "router"
    assert state.state == STATE_UNKNOWN

    # Test with invalid GPS accuracy should default to 0,
    # but location updates as expected
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude": 32.871234,"longitude": -117.21234, "gps_accuracy": "invalid", "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert state.state == STATE_NOT_HOME
    assert state.attributes["latitude"] == 32.871234
    assert state.attributes["longitude"] == -117.21234
    assert state.attributes["gps_accuracy"] == 0
    assert state.attributes["source_type"] == "router"

    # Test with invalid latitude
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude": null,"longitude": "-117.22743", "gps_accuracy": 1, "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.state == STATE_UNKNOWN

    # Test with invalid longitude
    async_fire_mqtt_message(
        hass,
        "attributes-topic",
        '{"latitude": 32.87336,"longitude": "unknown", "gps_accuracy": 1, "source_type": "router"}',
    )
    state = hass.states.get("device_tracker.test")
    assert "latitude" not in state.attributes
    assert "longitude" not in state.attributes
    assert state.state == STATE_UNKNOWN