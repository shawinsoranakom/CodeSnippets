async def test_multi_platform_discovery(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test setting up multiple platforms simultaneous."""
    await mqtt_mock_entry()
    entity_configs = {
        "alarm_control_panel": {
            "name": "test",
            "state_topic": "alarm/state",
            "command_topic": "alarm/command",
        },
        "button": {"name": "test", "command_topic": "test-topic"},
        "camera": {"name": "test", "topic": "test_topic"},
        "cover": {"name": "test", "state_topic": "test-topic"},
        "device_tracker": {
            "name": "test",
            "state_topic": "test-topic",
        },
        "fan": {
            "name": "test",
            "state_topic": "state-topic",
            "command_topic": "command-topic",
        },
        "sensor": {"name": "test", "state_topic": "test-topic"},
        "switch": {"name": "test", "command_topic": "test-topic"},
        "select": {
            "name": "test",
            "command_topic": "test-topic",
            "options": ["milk", "beer"],
        },
    }
    non_entity_configs = {
        "tag": {
            "device": {"identifiers": ["tag_0AFFD2"]},
            "topic": "foobar/tag_scanned",
        },
        "device_automation": {
            "automation_type": "trigger",
            "device": {"identifiers": ["device_automation_0AFFD2"]},
            "payload": "short_press",
            "topic": "foobar/triggers/button1",
            "type": "button_short_press",
            "subtype": "button_1",
        },
    }
    for platform, config in entity_configs.items():
        for set_number in range(2):
            set_config = deepcopy(config)
            set_config["name"] = f"test_{set_number}"
            topic = f"homeassistant/{platform}/bla_{set_number}/config"
            async_fire_mqtt_message(hass, topic, json.dumps(set_config))
    for platform, config in non_entity_configs.items():
        topic = f"homeassistant/{platform}/bla/config"
        async_fire_mqtt_message(hass, topic, json.dumps(config))
    await hass.async_block_till_done()
    for set_number in range(2):
        for platform in entity_configs:
            entity_id = f"{platform}.test_{set_number}"
            state = hass.states.get(entity_id)
            assert state is not None
    for platform in non_entity_configs:
        assert (
            device_registry.async_get_device(
                identifiers={("mqtt", f"{platform}_0AFFD2")}
            )
            is not None
        )