async def test_discovery_with_default_entity_id_for_previous_deleted_entity(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test discovering an MQTT entity with default_entity_id and unique_id."""

    topic = "homeassistant/sensor/object/bla/config"
    config = (
        '{ "name": "Hello World 11", "unique_id": "very_unique", '
        '"def_ent_id": "sensor.hello_id", "state_topic": "test-topic" }'
    )
    new_config = (
        '{ "name": "Hello World 11", "unique_id": "very_unique", '
        '"def_ent_id": "sensor.updated_hello_id", "state_topic": "test-topic" }'
    )
    initial_entity_id = "sensor.hello_id"
    new_entity_id = "sensor.updated_hello_id"
    later_entity_id = "sensor.later_hello_id"
    name = "Hello World 11"
    domain = "sensor"

    await mqtt_mock_entry()
    async_fire_mqtt_message(hass, topic, config)
    await hass.async_block_till_done()

    state = hass.states.get(initial_entity_id)

    assert state is not None
    assert state.name == name
    assert (domain, "object bla") in hass.data["mqtt"].discovery_already_discovered

    # Delete the entity
    async_fire_mqtt_message(hass, topic, "")
    await hass.async_block_till_done()
    assert (domain, "object bla") not in hass.data["mqtt"].discovery_already_discovered

    # Rediscover with new default_entity_id
    async_fire_mqtt_message(hass, topic, new_config)
    await hass.async_block_till_done()

    state = hass.states.get(new_entity_id)

    assert state is not None
    assert state.name == name
    assert (domain, "object bla") in hass.data["mqtt"].discovery_already_discovered

    # Assert the entity ID can be changed later
    entity_registry.async_update_entity(new_entity_id, new_entity_id=later_entity_id)
    await hass.async_block_till_done()
    state = hass.states.get(later_entity_id)

    assert state is not None
    assert state.name == name