async def test_controlling_state_via_mqtt(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mqtt_mock: MqttMockHAClient,
    snapshot: SnapshotAssertion,
    setup_tasmota,
    sensor_config,
    entity_ids,
    messages,
) -> None:
    """Test state update via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    sensor_config = copy.deepcopy(sensor_config)
    mac = config["mac"]

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()
    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{mac}/sensors",
        json.dumps(sensor_config),
    )
    await hass.async_block_till_done()

    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state.state == "unavailable"
        assert not state.attributes.get(ATTR_ASSUMED_STATE)
        assert state == snapshot

        entry = entity_registry.async_get(entity_id)
        assert entry.disabled is False
        assert entry.disabled_by is None
        assert entry.entity_category is None
        assert entry == snapshot

    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/LWT", "Online")
    await hass.async_block_till_done()
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state.state == STATE_UNKNOWN
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Test periodic state update
    async_fire_mqtt_message(hass, "tasmota_49A3BC/tele/SENSOR", messages[0])
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state == snapshot

    # Test polled state update
    async_fire_mqtt_message(hass, "tasmota_49A3BC/stat/STATUS10", messages[1])
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state == snapshot