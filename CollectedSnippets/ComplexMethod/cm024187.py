async def test_entity_device_info_with_connection(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test MQTT device registry integration."""
    await mqtt_mock_entry()

    data = json.dumps(
        {
            "topic": "test-topic",
            "device": {
                "connections": [[dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12"]],
                "manufacturer": "Whatever",
                "name": "Beer",
                "model": "Glass",
                "hw_version": "rev1",
                "serial_number": "1234deadbeef",
                "sw_version": "0.1-beta",
            },
        }
    )
    async_fire_mqtt_message(hass, "homeassistant/tag/bla/config", data)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12")}
    )
    assert device is not None
    assert device.connections == {(dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12")}
    assert device.manufacturer == "Whatever"
    assert device.name == "Beer"
    assert device.model == "Glass"
    assert device.hw_version == "rev1"
    assert device.serial_number == "1234deadbeef"
    assert device.sw_version == "0.1-beta"