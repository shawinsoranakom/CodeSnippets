async def help_test_entity_id_update_discovery_update(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    domain: str,
    config: dict[str, Any],
    sensor_config: dict[str, Any] | None = None,
    object_id: str = "tasmota_test",
) -> None:
    """Test MQTT discovery update after entity_id is updated."""
    entity_reg = er.async_get(hass)

    config = copy.deepcopy(config)
    data = json.dumps(config)

    topic = get_topic_tele_will(config)

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{config[CONF_MAC]}/config", data)
    await hass.async_block_till_done()
    if sensor_config:
        async_fire_mqtt_message(
            hass,
            f"{DEFAULT_PREFIX}/{config[CONF_MAC]}/sensors",
            json.dumps(sensor_config),
        )
        await hass.async_block_till_done()

    async_fire_mqtt_message(hass, topic, config_get_state_online(config))
    await hass.async_block_till_done()
    state = hass.states.get(f"{domain}.{object_id}")
    assert state.state != STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, topic, config_get_state_offline(config))
    await hass.async_block_till_done()
    state = hass.states.get(f"{domain}.{object_id}")
    assert state.state == STATE_UNAVAILABLE

    entity_reg.async_update_entity(
        f"{domain}.{object_id}", new_entity_id=f"{domain}.milk"
    )
    await hass.async_block_till_done()
    assert hass.states.get(f"{domain}.milk")

    assert config[CONF_PREFIX][PREFIX_TELE] != "tele2"
    config[CONF_PREFIX][PREFIX_TELE] = "tele2"
    data = json.dumps(config)
    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{config[CONF_MAC]}/config", data)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids(domain)) == 1

    topic = get_topic_tele_will(config)
    async_fire_mqtt_message(hass, topic, config_get_state_online(config))
    await hass.async_block_till_done()
    state = hass.states.get(f"{domain}.milk")
    assert state.state != STATE_UNAVAILABLE