async def test_debug_info_multiple_devices(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test we get correct debug_info when multiple devices are present."""
    await mqtt_mock_entry()
    devices: list[_DebugInfo] = [
        {
            "domain": "sensor",
            "config": {
                "device": {"identifiers": ["0AFFD0"]},
                "platform": "mqtt",
                "state_topic": "test-topic-sensor",
                "unique_id": "unique",
            },
        },
        {
            "domain": "binary_sensor",
            "config": {
                "device": {"identifiers": ["0AFFD1"]},
                "platform": "mqtt",
                "state_topic": "test-topic-binary-sensor",
                "unique_id": "unique",
            },
        },
        {
            "domain": "device_automation",
            "config": {
                "automation_type": "trigger",
                "device": {"identifiers": ["0AFFD2"]},
                "platform": "mqtt",
                "topic": "test-topic1",
                "type": "foo",
                "subtype": "bar",
            },
        },
        {
            "domain": "device_automation",
            "config": {
                "automation_type": "trigger",
                "device": {"identifiers": ["0AFFD3"]},
                "platform": "mqtt",
                "topic": "test-topic2",
                "type": "ikk",
                "subtype": "baz",
            },
        },
    ]

    for dev in devices:
        data = json.dumps(dev["config"])
        domain = dev["domain"]
        device_id = dev["config"]["device"]["identifiers"][0]
        async_fire_mqtt_message(
            hass, f"homeassistant/{domain}/{device_id}/config", data
        )
        await hass.async_block_till_done()

    for dev in devices:
        domain = dev["domain"]
        device_id = dev["config"]["device"]["identifiers"][0]
        device = device_registry.async_get_device(identifiers={("mqtt", device_id)})
        assert device is not None

        debug_info_data = debug_info.info_for_device(hass, device.id)
        if dev["domain"] != "device_automation":
            assert len(debug_info_data["entities"]) == 1
            assert len(debug_info_data["triggers"]) == 0
            discovery_data = debug_info_data["entities"][0]["discovery_data"]
            assert len(debug_info_data["entities"][0]["subscriptions"]) == 1
            topic = dev["config"]["state_topic"]
            assert {"topic": topic, "messages": []} in debug_info_data["entities"][0][
                "subscriptions"
            ]
        else:
            assert len(debug_info_data["entities"]) == 0
            assert len(debug_info_data["triggers"]) == 1
            discovery_data = debug_info_data["triggers"][0]["discovery_data"]

        assert discovery_data["topic"] == f"homeassistant/{domain}/{device_id}/config"
        assert discovery_data["payload"] == dev["config"]