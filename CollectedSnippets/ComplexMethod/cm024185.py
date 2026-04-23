async def test_shared_state_topic(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    discovery_topic: str,
    discovery_payload: str,
    entity_ids: list[str],
) -> None:
    """Test a shared state_topic can be used."""
    await mqtt_mock_entry()

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
        assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "foobar/sensor-shared", "New state")

    entity_id = entity_ids[0]
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "New state"
    entity_id = entity_ids[1]
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "New state"
    entity_id = entity_ids[2]
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "foobar/sensor3", "New state3")
    entity_id = entity_ids[2]
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "New state3"