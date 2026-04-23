async def test_cleanup_device_mqtt_device_discovery(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test discovered device is cleaned up partly when removed through MQTT."""
    await mqtt_mock_entry()

    discovery_topic = "homeassistant/device/bla/config"
    discovery_payload = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "o": {"name": "foobar"},'
        '  "cmps": {"sens1": {'
        '  "p": "sensor",'
        '  "name": "sensor1",'
        '  "state_topic": "foobar/sensor1",'
        '  "unique_id": "unique1"'
        ' },"sens2": {'
        '  "p": "sensor",'
        '  "name": "sensor2",'
        '  "state_topic": "foobar/sensor2",'
        '  "unique_id": "unique2"'
        "}}}"
    )
    entity_ids = ["sensor.sensor1", "sensor.sensor2"]
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

    # Do update and remove sensor 2 from device
    discovery_payload_update1 = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "o": {"name": "foobar"},'
        '  "cmps": {"sens1": {'
        '  "p": "sensor",'
        '  "name": "sensor1",'
        '  "state_topic": "foobar/sensor1",'
        '  "unique_id": "unique1"'
        ' },"sens2": {'
        '  "p": "sensor"'
        "}}}"
    )
    async_fire_mqtt_message(hass, discovery_topic, discovery_payload_update1)
    await hass.async_block_till_done()
    state = hass.states.get(entity_ids[0])
    assert state is not None
    state = hass.states.get(entity_ids[1])
    assert state is None

    # Repeating the update
    async_fire_mqtt_message(hass, discovery_topic, discovery_payload_update1)
    await hass.async_block_till_done()
    state = hass.states.get(entity_ids[0])
    assert state is not None
    state = hass.states.get(entity_ids[1])
    assert state is None

    # Removing last sensor
    discovery_payload_update2 = (
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "o": {"name": "foobar"},'
        '  "cmps": {"sens1": {'
        '  "p": "sensor"'
        ' },"sens2": {'
        '  "p": "sensor"'
        "}}}"
    )
    async_fire_mqtt_message(hass, discovery_topic, discovery_payload_update2)
    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    # Verify the device entry was removed with the last sensor
    assert device_entry is None
    for entity_id in entity_ids:
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry is None

        state = hass.states.get(entity_id)
        assert state is None

    # Repeating the update
    async_fire_mqtt_message(hass, discovery_topic, discovery_payload_update2)
    await hass.async_block_till_done()

    # Clear the empty discovery payload and verify there was nothing to cleanup
    async_fire_mqtt_message(hass, discovery_topic, "")
    await hass.async_block_till_done()
    assert "No device components to cleanup" in caplog.text