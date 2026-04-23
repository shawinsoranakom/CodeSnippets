async def test_cleanup_device_mqtt(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    discovery_topic: str,
    discovery_payload: str,
    entity_ids: list[str],
) -> None:
    """Test discovered device is cleaned up when removed through MQTT."""
    mqtt_mock = await mqtt_mock_entry()

    # set up an existing sensor first
    data = (
        '{ "device":{"identifiers":["0AFFD3"]},'
        '  "name": "sensor_base",'
        '  "state_topic": "foobar/sensor",'
        '  "unique_id": "unique_base" }'
    )
    base_discovery_topic = "homeassistant/sensor/bla_base/config"
    base_entity_id = "sensor.sensor_base"
    async_fire_mqtt_message(hass, base_discovery_topic, data)
    await hass.async_block_till_done()

    # Verify the base entity has been created and it has a state
    base_device_entry = device_registry.async_get_device(
        identifiers={("mqtt", "0AFFD3")}
    )
    assert base_device_entry is not None
    entity_entry = entity_registry.async_get(base_entity_id)
    assert entity_entry is not None
    state = hass.states.get(base_entity_id)
    assert state is not None

    async_fire_mqtt_message(hass, discovery_topic, discovery_payload)
    await hass.async_block_till_done()

    # Verify device and registry entries are created
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is not None
    for entity_id in entity_ids:
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry is not None

        state = hass.states.get(entity_id)
        assert state is not None

    async_fire_mqtt_message(hass, discovery_topic, "")
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Verify device and registry entries are cleared
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is None

    for entity_id in entity_ids:
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry is None

        # Verify state is removed
        state = hass.states.get(entity_id)
        assert state is None
        await hass.async_block_till_done()

    # Verify retained discovery topics have not been cleared again
    mqtt_mock.async_publish.assert_not_called()

    # Verify the base entity still exists and it has a state
    base_device_entry = device_registry.async_get_device(
        identifiers={("mqtt", "0AFFD3")}
    )
    assert base_device_entry is not None
    entity_entry = entity_registry.async_get(base_entity_id)
    assert entity_entry is not None
    state = hass.states.get(base_entity_id)
    assert state is not None