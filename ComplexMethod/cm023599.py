async def help_test_entity_id_update_subscriptions(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    domain: str,
    config: dict[str, Any],
    topics: list[str] | None = None,
    sensor_config: dict[str, Any] | None = None,
    object_id: str = "tasmota_test",
) -> None:
    """Test MQTT subscriptions are managed when entity_id is updated."""
    entity_reg = er.async_get(hass)

    config = copy.deepcopy(config)
    data = json.dumps(config)

    mqtt_mock.async_subscribe.reset_mock()

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{config[CONF_MAC]}/config", data)
    await hass.async_block_till_done()
    if sensor_config:
        async_fire_mqtt_message(
            hass,
            f"{DEFAULT_PREFIX}/{config[CONF_MAC]}/sensors",
            json.dumps(sensor_config),
        )
        await hass.async_block_till_done()

    if not topics:
        topics = [get_topic_tele_state(config), get_topic_tele_will(config)]
    assert len(topics) > 0

    state = hass.states.get(f"{domain}.{object_id}")
    assert state is not None
    assert mqtt_mock.async_subscribe.call_count == len(topics)
    for topic in topics:
        mqtt_mock.async_subscribe.assert_any_call(topic, ANY, ANY, ANY, ANY)
    mqtt_mock.async_subscribe.reset_mock()

    entity_reg.async_update_entity(
        f"{domain}.{object_id}", new_entity_id=f"{domain}.milk"
    )
    await hass.async_block_till_done()

    state = hass.states.get(f"{domain}.{object_id}")
    assert state is None

    state = hass.states.get(f"{domain}.milk")
    assert state is not None
    for topic in topics:
        mqtt_mock.async_subscribe.assert_any_call(topic, ANY, ANY, ANY, ANY)