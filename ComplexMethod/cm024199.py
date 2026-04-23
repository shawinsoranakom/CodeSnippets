async def help_test_custom_availability_payload(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
    no_assumed_state: bool = False,
    state_topic: str | None = None,
    state_message: str | None = None,
) -> None:
    """Test availability by custom payload with defined topic.

    This is a test helper for the MqttAvailability mixin.
    """
    # Add availability settings to config
    config = copy.deepcopy(config)
    config[mqtt.DOMAIN][domain]["availability_topic"] = "availability-topic"
    config[mqtt.DOMAIN][domain]["payload_available"] = "good"
    config[mqtt.DOMAIN][domain]["payload_not_available"] = "nogood"
    with patch("homeassistant.config.load_yaml_config_file", return_value=config):
        await mqtt_mock_entry()

    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "availability-topic", "good")

    state = hass.states.get(f"{domain}.test")
    assert state and state.state != STATE_UNAVAILABLE
    if no_assumed_state:
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "availability-topic", "nogood")

    state = hass.states.get(f"{domain}.test")
    assert state and state.state == STATE_UNAVAILABLE

    if state_topic is not None and state_message is not None:
        async_fire_mqtt_message(hass, state_topic, state_message)

        state = hass.states.get(f"{domain}.test")
        assert state and state.state == STATE_UNAVAILABLE

        async_fire_mqtt_message(hass, "availability-topic", "good")

        state = hass.states.get(f"{domain}.test")
        assert state and state.state != STATE_UNAVAILABLE