async def help_test_default_availability_list_payload_all(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
    no_assumed_state: bool = False,
) -> None:
    """Test availability by default payload with defined topic.

    This is a test helper for the MqttAvailability mixin.
    """
    # Add availability settings to config
    config = copy.deepcopy(config)
    config[mqtt.DOMAIN][domain]["availability_mode"] = "all"
    config[mqtt.DOMAIN][domain]["availability"] = [
        {"topic": "availability-topic1"},
        {"topic": "availability-topic2"},
    ]
    with patch("homeassistant.config.load_yaml_config_file", return_value=config):
        await mqtt_mock_entry()

    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability-topic1", "online")

    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE
    if no_assumed_state:
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "availability-topic2", "online")

    state = hass.states.get(f"{domain}.test")
    assert state and state.state != STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability-topic2", "offline")

    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE
    if no_assumed_state:
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "availability-topic2", "online")

    state = hass.states.get(f"{domain}.test")
    assert state and state.state != STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability-topic1", "offline")

    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE
    if no_assumed_state:
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "availability-topic1", "online")

    state = hass.states.get(f"{domain}.test")
    assert state and state.state != STATE_UNAVAILABLE