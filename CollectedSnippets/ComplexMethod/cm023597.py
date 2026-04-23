async def help_test_availability_discovery_update(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    domain: str,
    config: dict[str, Any],
    sensor_config: dict[str, Any] | None = None,
    object_id: str = "tasmota_test",
) -> None:
    """Test update of discovered TasmotaAvailability.

    This is a test helper for the TasmotaAvailability mixin.
    """
    # customize availability topic
    config1 = copy.deepcopy(config)
    config1[CONF_PREFIX][PREFIX_TELE] = "tele1"
    config1[CONF_OFFLINE] = "offline1"
    config1[CONF_ONLINE] = "online1"
    config2 = copy.deepcopy(config)
    config2[CONF_PREFIX][PREFIX_TELE] = "tele2"
    config2[CONF_OFFLINE] = "offline2"
    config2[CONF_ONLINE] = "online2"
    data1 = json.dumps(config1)
    data2 = json.dumps(config2)

    availability_topic1 = get_topic_tele_will(config1)
    availability_topic2 = get_topic_tele_will(config2)
    assert availability_topic1 != availability_topic2
    offline1 = config_get_state_offline(config1)
    offline2 = config_get_state_offline(config2)
    assert offline1 != offline2
    online1 = config_get_state_online(config1)
    online2 = config_get_state_online(config2)
    assert online1 != online2

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{config1[CONF_MAC]}/config", data1)
    await hass.async_block_till_done()
    if sensor_config:
        async_fire_mqtt_message(
            hass,
            f"{DEFAULT_PREFIX}/{config[CONF_MAC]}/sensors",
            json.dumps(sensor_config),
        )
        await hass.async_block_till_done()

    state = hass.states.get(f"{domain}.{object_id}")
    assert state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, availability_topic1, online1)
    await hass.async_block_till_done()
    state = hass.states.get(f"{domain}.{object_id}")
    assert state.state != STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, availability_topic1, offline1)
    await hass.async_block_till_done()
    state = hass.states.get(f"{domain}.{object_id}")
    assert state.state == STATE_UNAVAILABLE

    # Change availability settings
    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{config2[CONF_MAC]}/config", data2)
    await hass.async_block_till_done()

    # Verify we are no longer subscribing to the old topic or payload
    async_fire_mqtt_message(hass, availability_topic1, online1)
    async_fire_mqtt_message(hass, availability_topic1, online2)
    async_fire_mqtt_message(hass, availability_topic2, online1)
    await hass.async_block_till_done()
    state = hass.states.get(f"{domain}.{object_id}")
    assert state.state == STATE_UNAVAILABLE

    # Verify we are subscribing to the new topic
    async_fire_mqtt_message(hass, availability_topic2, online2)
    await hass.async_block_till_done()
    state = hass.states.get(f"{domain}.{object_id}")
    assert state.state != STATE_UNAVAILABLE