async def test_cleanup_tag(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test tag discovery topic is cleaned when device is removed from registry."""
    assert await async_setup_component(hass, "config", {})
    await hass.async_block_till_done()
    mqtt_mock = await mqtt_mock_entry()
    ws_client = await hass_ws_client(hass)

    mqtt_entry = hass.config_entries.async_entries("mqtt")[0]

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections=set(),
        identifiers={("mqtt", "helloworld")},
    )

    config1 = {
        "topic": "test-topic",
        "device": {"identifiers": ["helloworld"]},
    }
    config2 = {
        "topic": "test-topic",
        "device": {"identifiers": ["hejhopp"]},
    }

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    async_fire_mqtt_message(hass, "homeassistant/tag/bla1/config", data1)
    await hass.async_block_till_done()
    async_fire_mqtt_message(hass, "homeassistant/tag/bla2/config", data2)
    await hass.async_block_till_done()

    # Verify device registry entries are created
    device_entry1 = device_registry.async_get_device(
        identifiers={("mqtt", "helloworld")}
    )
    assert device_entry1 is not None
    assert device_entry1.config_entries == {config_entry.entry_id, mqtt_entry.entry_id}
    device_entry2 = device_registry.async_get_device(identifiers={("mqtt", "hejhopp")})
    assert device_entry2 is not None

    # Remove other config entry from the device
    device_registry.async_update_device(
        device_entry1.id, remove_config_entry_id=config_entry.entry_id
    )
    device_entry1 = device_registry.async_get_device(
        identifiers={("mqtt", "helloworld")}
    )
    assert device_entry1 is not None
    assert device_entry1.config_entries == {mqtt_entry.entry_id}
    device_entry2 = device_registry.async_get_device(identifiers={("mqtt", "hejhopp")})
    assert device_entry2 is not None
    mqtt_mock.async_publish.assert_not_called()

    # Remove MQTT from the device
    mqtt_config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    response = await ws_client.remove_device(
        device_entry1.id, mqtt_config_entry.entry_id
    )
    assert response["success"]
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Verify device registry entry is cleared
    device_entry1 = device_registry.async_get_device(
        identifiers={("mqtt", "helloworld")}
    )
    assert device_entry1 is None
    device_entry2 = device_registry.async_get_device(identifiers={("mqtt", "hejhopp")})
    assert device_entry2 is not None

    # Verify retained discovery topic has been cleared
    mqtt_mock.async_publish.assert_called_once_with(
        "homeassistant/tag/bla1/config", None, 0, True
    )