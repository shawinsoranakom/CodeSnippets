async def test_cleanup_device_tracker(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test discovered device is cleaned up when removed from registry."""
    assert await async_setup_component(hass, "config", {})
    await hass.async_block_till_done()
    mqtt_mock = await mqtt_mock_entry()
    ws_client = await hass_ws_client(hass)

    async_fire_mqtt_message(
        hass,
        "homeassistant/device_tracker/bla/config",
        '{ "device":{"identifiers":["0AFFD2"]},'
        '  "state_topic": "foobar/tracker",'
        '  "unique_id": "unique" }',
    )
    await hass.async_block_till_done()

    # Verify device and registry entries are created
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is not None
    entity_entry = entity_registry.async_get("device_tracker.mqtt_unique")
    assert entity_entry is not None

    state = hass.states.get("device_tracker.mqtt_unique")
    assert state is not None

    # Remove MQTT from the device
    mqtt_config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    response = await ws_client.remove_device(
        device_entry.id, mqtt_config_entry.entry_id
    )
    assert response["success"]
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Verify device and registry entries are cleared
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is None
    entity_entry = entity_registry.async_get("device_tracker.mqtt_unique")
    assert entity_entry is None

    # Verify state is removed
    state = hass.states.get("device_tracker.mqtt_unique")
    assert state is None
    await hass.async_block_till_done()

    # Verify retained discovery topic has been cleared
    mqtt_mock.async_publish.assert_called_once_with(
        "homeassistant/device_tracker/bla/config", None, 0, True
    )