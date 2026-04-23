async def test_registry_enable_not_enabled_by_default_entity(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test enabling an entity that was not enabled by default."""
    await mqtt_mock_entry()

    discovery_topic = "homeassistant/sensor/bla/config"
    config_disabled = json.json_dumps(
        {
            "name": None,
            "state_topic": "state-topic",
            "enabled_by_default": False,
            "unique_id": "very_unique",
            "default_entity_id": "sensor.test",
            "device": {"identifiers": "very_unique_device", "name": "test"},
        }
    )
    config_enabled = json.json_dumps(
        {
            "name": None,
            "state_topic": "state-topic",
            "enabled_by_default": True,
            "unique_id": "very_unique",
            "default_entity_id": "sensor.test",
            "device": {"identifiers": "very_unique_device", "name": "test"},
        }
    )
    config_enabled_new_entity_name = json.json_dumps(
        {
            "name": None,
            "state_topic": "state-topic",
            "enabled_by_default": True,
            "unique_id": "very_unique",
            "default_entity_id": "sensor.test_new",
            "device": {"identifiers": "very_unique_device", "name": "test"},
        }
    )

    async_fire_mqtt_message(hass, discovery_topic, config_disabled)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test")
    assert state is None
    entry = entity_registry.async_get("sensor.test")
    assert entry is not None
    assert entry.disabled
    assert (device_id := entry.device_id)
    assert device_registry.async_get(device_id) is not None

    # Remove the entity and device
    # At this stage no entry existed during the initialization
    async_fire_mqtt_message(hass, discovery_topic, "")
    await hass.async_block_till_done(wait_background_tasks=True)
    entry = entity_registry.async_get("sensor.test")
    assert entry is None
    # Assert device is cleaned up
    assert device_registry.async_get(device_id) is None

    # Rediscover the previous deleted entity and allow it to be enabled
    async_fire_mqtt_message(hass, discovery_topic, config_enabled)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test")
    assert state is not None
    entry = entity_registry.async_get("sensor.test")
    assert entry is not None
    assert not entry.disabled
    assert device_registry.async_get(device_id) is not None

    # Update entity to not be enabled by default
    # The entity should stay available as it was enabled before
    async_fire_mqtt_message(hass, discovery_topic, config_disabled)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test")
    assert state is not None
    entry = entity_registry.async_get("sensor.test")
    assert entry is not None
    assert not entry.disabled
    assert device_registry.async_get(device_id) is not None

    # Delete the entity again
    async_fire_mqtt_message(hass, discovery_topic, "")
    await hass.async_block_till_done(wait_background_tasks=True)
    entry = entity_registry.async_get("sensor.test")
    assert entry is None
    # Assert device is cleaned up
    assert device_registry.async_get(device_id) is None

    # Repeat the re-discovery, with a new entity name
    async_fire_mqtt_message(hass, discovery_topic, config_enabled_new_entity_name)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.test_new")
    assert state is not None
    entry = entity_registry.async_get("sensor.test_new")
    assert entry is not None
    assert not entry.disabled
    assert device_registry.async_get(device_id) is not None