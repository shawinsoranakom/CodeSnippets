async def help_test_encoding_subscribable_topics(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    config: ConfigType,
    topic: str,
    value: Any,
    attribute: str | None = None,
    attribute_value: Any = None,
    init_payload: tuple[str, str] | None = None,
    skip_raw_test: bool = False,
) -> None:
    """Test handling of incoming encoded payload."""

    async def _test_encoding(
        hass: HomeAssistant,
        entity_id,
        topic,
        encoded_value,
        attribute,
        init_payload_topic,
        init_payload_value,
    ) -> Any:
        state = hass.states.get(entity_id)

        if init_payload_value:
            # Sometimes a device needs to have an initialization pay load, e.g. to switch the device on.
            async_fire_mqtt_message(hass, init_payload_topic, init_payload_value)
            await hass.async_block_till_done()

        state = hass.states.get(entity_id)

        async_fire_mqtt_message(hass, topic, encoded_value)
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state is not None

        if attribute:
            return state.attributes.get(attribute)

        return state.state if state else None

    init_payload_value_utf8 = None
    init_payload_value_utf16 = None
    # setup test1 default encoding
    config1 = copy.deepcopy(config)
    if domain == "device_tracker":
        config1["unique_id"] = "test1"
    else:
        config1["name"] = "test1"
    config1[topic] = "topic/test1"
    # setup test2 alternate encoding
    config2 = copy.deepcopy(config)
    if domain == "device_tracker":
        config2["unique_id"] = "test2"
    else:
        config2["name"] = "test2"
    config2["encoding"] = "utf-16"
    config2[topic] = "topic/test2"
    # setup test3 raw encoding
    config3 = copy.deepcopy(config)
    if domain == "device_tracker":
        config3["unique_id"] = "test3"
    else:
        config3["name"] = "test3"
    config3["encoding"] = ""
    config3[topic] = "topic/test3"

    if init_payload:
        config1[init_payload[0]] = "topic/init_payload1"
        config2[init_payload[0]] = "topic/init_payload2"
        config3[init_payload[0]] = "topic/init_payload3"
        init_payload_value_utf8 = init_payload[1].encode("utf-8")
        init_payload_value_utf16 = init_payload[1].encode("utf-16")

    await mqtt_mock_entry()
    async_fire_mqtt_message(
        hass, f"homeassistant/{domain}/item1/config", json.dumps(config1)
    )
    async_fire_mqtt_message(
        hass, f"homeassistant/{domain}/item2/config", json.dumps(config2)
    )
    async_fire_mqtt_message(
        hass, f"homeassistant/{domain}/item3/config", json.dumps(config3)
    )
    await hass.async_block_till_done()

    expected_result = attribute_value or value

    # test1 default encoding
    assert (
        await _test_encoding(
            hass,
            f"{domain}.test1",
            "topic/test1",
            value.encode("utf-8"),
            attribute,
            "topic/init_payload1",
            init_payload_value_utf8,
        )
        == expected_result
    )

    # test2 alternate encoding
    assert (
        await _test_encoding(
            hass,
            f"{domain}.test2",
            "topic/test2",
            value.encode("utf-16"),
            attribute,
            "topic/init_payload2",
            init_payload_value_utf16,
        )
        == expected_result
    )

    # test3 raw encoded input
    if skip_raw_test:
        return

    with suppress(AttributeError, TypeError, ValueError):
        result = await _test_encoding(
            hass,
            f"{domain}.test3",
            "topic/test3",
            value.encode("utf-16"),
            attribute,
            "topic/init_payload3",
            init_payload_value_utf16,
        )
        assert result != expected_result