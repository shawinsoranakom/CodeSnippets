async def help_test_entity_id_update_subscriptions(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
    topics: list[str] | None = None,
) -> None:
    """Test MQTT subscriptions are managed when entity_id is updated."""
    # Add unique_id to config
    config = copy.deepcopy(config)
    config[mqtt.DOMAIN][domain]["unique_id"] = "TOTALLY_UNIQUE"

    if topics is None:
        # Add default topics to config
        config[mqtt.DOMAIN][domain]["availability_topic"] = "avty-topic"
        config[mqtt.DOMAIN][domain]["state_topic"] = "test-topic"
        topics = ["avty-topic", "test-topic"]
    assert len(topics) > 0
    entity_registry = er.async_get(hass)

    with patch("homeassistant.config.load_yaml_config_file", return_value=config):
        mqtt_mock = await mqtt_mock_entry()
    assert mqtt_mock is not None

    state = hass.states.get(f"{domain}.test")
    assert state is not None
    assert (
        mqtt_mock.async_subscribe.call_count
        == len(topics)
        + 2 * len(SUPPORTED_COMPONENTS)
        + DISCOVERY_COUNT
        + DEVICE_DISCOVERY_COUNT
    )
    for topic in topics:
        mqtt_mock.async_subscribe.assert_any_call(
            topic, ANY, ANY, ANY, HassJobType.Callback
        )
    mqtt_mock.async_subscribe.reset_mock()

    entity_registry.async_update_entity(
        f"{domain}.test", new_entity_id=f"{domain}.milk"
    )
    await hass.async_block_till_done()

    state = hass.states.get(f"{domain}.test")
    assert state is None

    state = hass.states.get(f"{domain}.milk")
    assert state is not None
    for topic in topics:
        mqtt_mock.async_subscribe.assert_any_call(
            topic, ANY, ANY, ANY, HassJobType.Callback
        )