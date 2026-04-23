async def help_test_discovery_update_availability(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
) -> None:
    """Test update of discovered MQTTAvailability.

    This is a test helper for the MQTTAvailability mixin.
    """
    await mqtt_mock_entry()
    # Add availability settings to config
    config1 = copy.deepcopy(config)
    config1[mqtt.DOMAIN][domain]["availability_topic"] = "availability-topic1"
    config2 = copy.deepcopy(config)
    config2[mqtt.DOMAIN][domain]["availability"] = [
        {"topic": "availability-topic2"},
        {"topic": "availability-topic3"},
    ]
    config3 = copy.deepcopy(config)
    config3[mqtt.DOMAIN][domain]["availability_topic"] = "availability-topic4"
    data1 = json.dumps(config1[mqtt.DOMAIN][domain])
    data2 = json.dumps(config2[mqtt.DOMAIN][domain])
    data3 = json.dumps(config3[mqtt.DOMAIN][domain])

    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", data1)
    await hass.async_block_till_done()

    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability-topic1", "online")
    state = hass.states.get(f"{domain}.test")
    assert state and state.state != STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability-topic1", "offline")
    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    # Change availability_topic
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", data2)
    await hass.async_block_till_done()

    # Verify we are no longer subscribing to the old topic
    async_fire_mqtt_message(hass, "availability-topic1", "online")
    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    # Verify we are subscribing to the new topic
    async_fire_mqtt_message(hass, "availability-topic2", "online")
    state = hass.states.get(f"{domain}.test")
    assert state and state.state != STATE_UNAVAILABLE

    # Verify we are subscribing to the new topic
    async_fire_mqtt_message(hass, "availability-topic3", "offline")
    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    # Change availability_topic
    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", data3)
    await hass.async_block_till_done()

    # Verify we are no longer subscribing to the old topic
    async_fire_mqtt_message(hass, "availability-topic2", "online")
    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    # Verify we are no longer subscribing to the old topic
    async_fire_mqtt_message(hass, "availability-topic3", "online")
    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    # Verify we are subscribing to the new topic
    async_fire_mqtt_message(hass, "availability-topic4", "online")
    state = hass.states.get(f"{domain}.test")
    assert state and state.state != STATE_UNAVAILABLE