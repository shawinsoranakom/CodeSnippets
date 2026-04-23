async def test_discovery_migration_to_device_base(
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
    """Test the migration of single discovery to device discovery."""
    await mqtt_mock_entry()

    # Discovery single config schema
    for discovery_topic, config in single_configs:
        payload = json.dumps(config)
        async_fire_mqtt_message(
            hass,
            discovery_topic,
            payload,
        )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    await help_check_discovered_items(hass, device_registry, tag_mock)

    # Try to migrate to device based discovery without migrate_discovery flag
    payload = json.dumps(device_config)
    async_fire_mqtt_message(
        hass,
        device_discovery_topic,
        payload,
    )
    await hass.async_block_till_done()
    assert (
        "Received a conflicting MQTT discovery message for device_automation "
        "'0AFFD2 bla1' which was previously discovered on topic homeassistant/"
        "device_automation/0AFFD2/bla1/config from external application Foo2Mqtt, "
        "version: 1.40.2; the conflicting discovery message was received on topic "
        "homeassistant/device/0AFFD2/config from external application Foo2Mqtt, "
        "version: 1.50.0; for support visit https://www.foo2mqtt.io" in caplog.text
    )
    assert (
        "Received a conflicting MQTT discovery message for entity sensor."
        "test_device_mqtt_sensor; the entity was previously discovered on topic "
        "homeassistant/sensor/0AFFD2/bla2/config from external application Foo2Mqtt, "
        "version: 1.40.2; the conflicting discovery message was received on topic "
        "homeassistant/device/0AFFD2/config from external application Foo2Mqtt, "
        "version: 1.50.0; for support visit https://www.foo2mqtt.io" in caplog.text
    )
    assert (
        "Received a conflicting MQTT discovery message for tag '0AFFD2 bla3' which "
        "was previously discovered on topic homeassistant/tag/0AFFD2/bla3/config "
        "from external application Foo2Mqtt, version: 1.40.2; the conflicting "
        "discovery message was received on topic homeassistant/device/0AFFD2/config "
        "from external application Foo2Mqtt, version: 1.50.0; for support visit "
        "https://www.foo2mqtt.io" in caplog.text
    )

    # Check we still have our mqtt items
    await help_check_discovered_items(hass, device_registry, tag_mock)

    # Test Enable discovery migration
    # Discovery single config schema
    caplog.clear()
    for discovery_topic, _ in single_configs:
        # migr_discvry is abbreviation for migrate_discovery
        payload = json.dumps({"migr_discvry": True})
        async_fire_mqtt_message(
            hass,
            discovery_topic,
            payload,
        )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Assert we still have our device entry
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is not None
    # Check our trigger was unloaden
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert len(triggers) == 0
    # Check the sensor was unloaded
    state = hass.states.get("sensor.test_device_mqtt_sensor")
    assert state is None
    # Check the entity registry entry is retained
    assert entity_registry.async_is_registered("sensor.test_device_mqtt_sensor")

    assert (
        "Migration to MQTT device discovery schema started for device_automation "
        "'0AFFD2 bla1' from external application Foo2Mqtt, version: 1.40.2 on topic "
        "homeassistant/device_automation/0AFFD2/bla1/config. To complete migration, "
        "publish a device discovery message with device_automation '0AFFD2 bla1'. "
        "After completed migration, publish an empty (retained) payload to "
        "homeassistant/device_automation/0AFFD2/bla1/config" in caplog.text
    )
    assert (
        "Migration to MQTT device discovery schema started for entity sensor."
        "test_device_mqtt_sensor from external application Foo2Mqtt, version: 1.40.2 "
        "on topic homeassistant/sensor/0AFFD2/bla2/config. To complete migration, "
        "publish a device discovery message with sensor entity '0AFFD2 bla2'. After "
        "completed migration, publish an empty (retained) payload to "
        "homeassistant/sensor/0AFFD2/bla2/config" in caplog.text
    )

    # Migrate to device based discovery
    caplog.clear()
    payload = json.dumps(device_config)
    async_fire_mqtt_message(
        hass,
        device_discovery_topic,
        payload,
    )
    await hass.async_block_till_done()

    caplog.clear()
    for _ in range(2):
        # Test publishing an empty payload twice to the migrated discovery topics
        # does not remove the migrated items
        for discovery_topic, _ in single_configs:
            async_fire_mqtt_message(
                hass,
                discovery_topic,
                "",
            )
        await hass.async_block_till_done()
        await hass.async_block_till_done()

        # Check we still have our mqtt items after publishing an
        # empty payload to the old discovery topics
        await help_check_discovered_items(hass, device_registry, tag_mock)

    # Check we cannot accidentally migrate back and remove the items
    caplog.clear()
    for discovery_topic, config in single_configs:
        payload = json.dumps(config)
        async_fire_mqtt_message(
            hass,
            discovery_topic,
            payload,
        )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert (
        "Received a conflicting MQTT discovery message for device_automation "
        "'0AFFD2 bla1' which was previously discovered on topic homeassistant/device"
        "/0AFFD2/config from external application Foo2Mqtt, version: 1.50.0; the "
        "conflicting discovery message was received on topic homeassistant/"
        "device_automation/0AFFD2/bla1/config from external application Foo2Mqtt, "
        "version: 1.40.2; for support visit https://www.foo2mqtt.io" in caplog.text
    )
    assert (
        "Received a conflicting MQTT discovery message for entity sensor."
        "test_device_mqtt_sensor; the entity was previously discovered on topic "
        "homeassistant/device/0AFFD2/config from external application Foo2Mqtt, "
        "version: 1.50.0; the conflicting discovery message was received on topic "
        "homeassistant/sensor/0AFFD2/bla2/config from external application Foo2Mqtt, "
        "version: 1.40.2; for support visit https://www.foo2mqtt.io" in caplog.text
    )
    assert (
        "Received a conflicting MQTT discovery message for tag '0AFFD2 bla3' which was "
        "previously discovered on topic homeassistant/device/0AFFD2/config from "
        "external application Foo2Mqtt, version: 1.50.0; the conflicting discovery "
        "message was received on topic homeassistant/tag/0AFFD2/bla3/config from "
        "external application Foo2Mqtt, version: 1.40.2; for support visit "
        "https://www.foo2mqtt.io" in caplog.text
    )

    caplog.clear()
    for discovery_topic, config in single_configs:
        payload = json.dumps(config)
        async_fire_mqtt_message(
            hass,
            discovery_topic,
            "",
        )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Check we still have our mqtt items after publishing an
    # empty payload to the old discovery topics
    await help_check_discovered_items(hass, device_registry, tag_mock)

    # Check we can remove the config using the new discovery topic
    async_fire_mqtt_message(
        hass,
        device_discovery_topic,
        "",
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    # Check the device was removed as all device components were removed
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is None
    await hass.async_block_till_done(wait_background_tasks=True)