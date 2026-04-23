async def test_cleanup_device_multiple_config_entries(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test discovered device is cleaned up when entry removed from device."""
    assert await async_setup_component(hass, "config", {})
    await hass.async_block_till_done()
    mqtt_mock = await mqtt_mock_entry()
    ws_client = await hass_ws_client(hass)

    config_entry = MockConfigEntry(
        domain="test",
        data={},
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={("mac", "12:34:56:AB:CD:EF")},
    )
    assert device_entry is not None

    mqtt_config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]

    sensor_config = {
        "device": {"connections": [["mac", "12:34:56:AB:CD:EF"]]},
        "state_topic": "foobar/sensor",
        "unique_id": "unique",
    }
    tag_config = {
        "device": {"connections": [["mac", "12:34:56:AB:CD:EF"]]},
        "topic": "test-topic",
    }
    trigger_config = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {"connections": [["mac", "12:34:56:AB:CD:EF"]]},
    }

    sensor_data = json.dumps(sensor_config)
    tag_data = json.dumps(tag_config)
    trigger_data = json.dumps(trigger_config)
    async_fire_mqtt_message(hass, "homeassistant/sensor/bla/config", sensor_data)
    async_fire_mqtt_message(hass, "homeassistant/tag/bla/config", tag_data)
    async_fire_mqtt_message(
        hass, "homeassistant/device_automation/bla/config", trigger_data
    )
    await hass.async_block_till_done()

    # Verify device and registry entries are created
    device_entry = device_registry.async_get_device(
        connections={("mac", "12:34:56:AB:CD:EF")}
    )
    assert device_entry is not None
    assert device_entry.config_entries == {
        mqtt_config_entry.entry_id,
        config_entry.entry_id,
    }
    entity_entry = entity_registry.async_get("sensor.mqtt_sensor")
    assert entity_entry is not None

    state = hass.states.get("sensor.mqtt_sensor")
    assert state is not None

    # Remove MQTT from the device
    mqtt_config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    response = await ws_client.remove_device(
        device_entry.id, mqtt_config_entry.entry_id
    )
    assert response["success"]

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Verify device is still there but entity is cleared
    device_entry = device_registry.async_get_device(
        connections={("mac", "12:34:56:AB:CD:EF")}
    )
    assert device_entry is not None
    entity_entry = entity_registry.async_get("sensor.mqtt_sensor")
    assert device_entry.config_entries == {config_entry.entry_id}
    assert entity_entry is None

    # Verify state is removed
    state = hass.states.get("sensor.mqtt_sensor")
    assert state is None
    await hass.async_block_till_done()

    # Verify retained discovery topic has been cleared
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("homeassistant/sensor/bla/config", None, 0, True),
            call("homeassistant/tag/bla/config", None, 0, True),
            call("homeassistant/device_automation/bla/config", None, 0, True),
        ],
        any_order=True,
    )