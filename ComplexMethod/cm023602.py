async def test_quantity_override(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mqtt_mock: MqttMockHAClient,
    setup_tasmota,
    sensor_config,
    entity_ids,
    states,
) -> None:
    """Test quantity override for certain sensors."""
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
        expected_state = states[entity_id]
        for attribute, expected in expected_state.get("attributes", {}).items():
            assert state.attributes.get(attribute) == expected

        entry = entity_registry.async_get(entity_id)
        assert entry.disabled is False
        assert entry.disabled_by is None
        assert entry.entity_category is None