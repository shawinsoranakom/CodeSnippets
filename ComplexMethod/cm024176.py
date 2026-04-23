async def test_cleanup_device_manual(
    hass: HomeAssistant,
    mock_debouncer: asyncio.Event,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    discovery_payloads: dict[str, str],
    entity_ids: list[str],
) -> None:
    """Test discovered device is cleaned up when entry removed from device."""
    mqtt_mock = await mqtt_mock_entry()
    assert await async_setup_component(hass, "config", {})
    ws_client = await hass_ws_client(hass)

    mock_debouncer.clear()
    for discovery_topic, discovery_payload in discovery_payloads.items():
        async_fire_mqtt_message(hass, discovery_topic, discovery_payload)
    await mock_debouncer.wait()

    # Verify device and registry entries are created
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is not None

    for entity_id in entity_ids:
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry is not None

        state = hass.states.get(entity_id)
        assert state is not None

    # Remove MQTT from the device
    mqtt_config_entry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    mock_debouncer.clear()
    response = await ws_client.remove_device(
        device_entry.id, mqtt_config_entry.entry_id
    )
    assert response["success"]
    await mock_debouncer.wait()
    await hass.async_block_till_done()

    # Verify device and registry entries are cleared
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is None
    entity_entry = entity_registry.async_get("sensor.mqtt_sensor")
    assert entity_entry is None

    # Verify state is removed
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state is None

    # Verify retained discovery topics have been cleared
    mqtt_mock.async_publish.assert_has_calls(
        [call(discovery_topic, None, 0, True) for discovery_topic in discovery_payloads]
    )

    await hass.async_block_till_done(wait_background_tasks=True)