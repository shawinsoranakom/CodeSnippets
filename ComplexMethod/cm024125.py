async def test_debug_info_multiple_entities_triggers(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test we get correct debug_info for a device with multiple entities and triggers."""
    await mqtt_mock_entry()
    config: list[_DebugInfo] = [
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
                "device": {"identifiers": ["0AFFD0"]},
                "platform": "mqtt",
                "state_topic": "test-topic-binary-sensor",
                "unique_id": "unique",
            },
        },
        {
            "domain": "device_automation",
            "config": {
                "automation_type": "trigger",
                "device": {"identifiers": ["0AFFD0"]},
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
                "device": {"identifiers": ["0AFFD0"]},
                "platform": "mqtt",
                "topic": "test-topic2",
                "type": "ikk",
                "subtype": "baz",
            },
        },
    ]

    for c in config:
        data = json.dumps(c["config"])
        domain = c["domain"]
        # Use topic as discovery_id
        discovery_id = c["config"].get("topic", c["config"].get("state_topic"))
        async_fire_mqtt_message(
            hass, f"homeassistant/{domain}/{discovery_id}/config", data
        )
        await hass.async_block_till_done()

    device_id = config[0]["config"]["device"]["identifiers"][0]
    device = device_registry.async_get_device(identifiers={("mqtt", device_id)})
    assert device is not None
    debug_info_data = debug_info.info_for_device(hass, device.id)
    assert len(debug_info_data["entities"]) == 2
    assert len(debug_info_data["triggers"]) == 2

    for c in config:
        # Test we get debug info for each entity and trigger
        domain = c["domain"]
        # Use topic as discovery_id
        discovery_id = c["config"].get("topic", c["config"].get("state_topic"))

        if c["domain"] != "device_automation":
            discovery_data = [e["discovery_data"] for e in debug_info_data["entities"]]
            topic = c["config"]["state_topic"]
            assert {"topic": topic, "messages": []} in [
                t for e in debug_info_data["entities"] for t in e["subscriptions"]
            ]
        else:
            discovery_data = [e["discovery_data"] for e in debug_info_data["triggers"]]

        assert {
            "topic": f"homeassistant/{domain}/{discovery_id}/config",
            "payload": c["config"],
        } in discovery_data