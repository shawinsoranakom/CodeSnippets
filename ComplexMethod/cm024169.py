async def test_discovery_rollback_to_single_base(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    tag_mock: AsyncMock,
    caplog: pytest.LogCaptureFixture,
    single_configs: list[tuple[str, dict[str, Any]]],
    device_discovery_topic: str,
    device_config: dict[str, Any],
) -> None:
    """Test the rollback of device discovery to a single component discovery."""
    await mqtt_mock_entry()

    # Start device based discovery
    # any single component discovery will be migrated
    payload = json.dumps(device_config)
    async_fire_mqtt_message(
        hass,
        device_discovery_topic,
        payload,
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    await help_check_discovered_items(hass, device_registry, tag_mock)

    # Migrate to single component discovery
    # Test the schema
    caplog.clear()
    payload = json.dumps({"migrate_discovery": "invalid"})
    async_fire_mqtt_message(
        hass,
        device_discovery_topic,
        payload,
    )
    await hass.async_block_till_done()
    assert "Invalid MQTT device discovery payload for 0AFFD2" in caplog.text

    # Set the correct migrate_discovery flag in the device payload
    # to allow rollback
    payload = json.dumps({"migrate_discovery": True})
    async_fire_mqtt_message(
        hass,
        device_discovery_topic,
        payload,
    )
    await hass.async_block_till_done()

    # Check the log messages
    assert (
        "Rollback to MQTT platform discovery schema started for entity sensor."
        "test_device_mqtt_sensor from external application Foo2Mqtt, version: 1.50.0 "
        "on topic homeassistant/device/0AFFD2/config. To complete rollback, publish a "
        "platform discovery message with sensor entity '0AFFD2 bla2'. After completed "
        "rollback, publish an empty (retained) payload to "
        "homeassistant/device/0AFFD2/config" in caplog.text
    )
    assert (
        "Rollback to MQTT platform discovery schema started for device_automation "
        "'0AFFD2 bla1' from external application Foo2Mqtt, version: 1.50.0 on topic "
        "homeassistant/device/0AFFD2/config. To complete rollback, publish a platform "
        "discovery message with device_automation '0AFFD2 bla1'. After completed "
        "rollback, publish an empty (retained) payload to "
        "homeassistant/device/0AFFD2/config" in caplog.text
    )

    # Assert we still have our device entry
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is not None
    # Check our trigger was unloaded
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert len(triggers) == 0
    # Check the sensor was unloaded
    state = hass.states.get("sensor.test_device_mqtt_sensor")
    assert state is None
    # Check the entity registry entry is retained
    assert entity_registry.async_is_registered("sensor.test_device_mqtt_sensor")

    # Publish the new component based payloads
    # to switch back to component based discovery
    for discovery_topic, config in single_configs:
        payload = json.dumps(config)
        async_fire_mqtt_message(
            hass,
            discovery_topic,
            payload,
        )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Check we still have our mqtt items
    # await help_check_discovered_items(hass, device_registry, tag_mock)

    for _ in range(2):
        # Test publishing an empty payload twice to the migrated discovery topic
        # does not remove the migrated items
        async_fire_mqtt_message(
            hass,
            device_discovery_topic,
            "",
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()

        # Check we still have our mqtt items after publishing an
        # empty payload to the old discovery topics
        await help_check_discovered_items(hass, device_registry, tag_mock)

    # Check we cannot accidentally migrate back and remove the items
    payload = json.dumps(device_config)
    async_fire_mqtt_message(
        hass,
        device_discovery_topic,
        payload,
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Check we still have our mqtt items after publishing an
    # empty payload to the old discovery topics
    await help_check_discovered_items(hass, device_registry, tag_mock)

    # Check we can remove the the config using the new discovery topics
    for discovery_topic, config in single_configs:
        payload = json.dumps(config)
        async_fire_mqtt_message(
            hass,
            discovery_topic,
            "",
        )
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    # Check the device was removed as all device components were removed
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is None