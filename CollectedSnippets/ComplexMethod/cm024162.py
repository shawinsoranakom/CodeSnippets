async def test_trigger_debug_info(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test debug_info.

    This is a test helper for MQTT debug_info.
    """
    await mqtt_mock_entry()

    config1 = {
        "platform": "mqtt",
        "automation_type": "trigger",
        "topic": "test-topic1",
        "type": "foo",
        "subtype": "bar1",
        "device": {
            "connections": [[dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12"]],
            "manufacturer": "Whatever",
            "name": "Beer",
            "model": "Glass",
            "sw_version": "0.1-beta",
        },
    }
    config2 = {
        "platform": "mqtt",
        "automation_type": "trigger",
        "topic": "test-topic2",
        "type": "foo",
        "subtype": "bar2",
        "device": {
            "connections": [[dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12"]],
        },
    }
    data = json.dumps(config1)
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", data)
    data = json.dumps(config2)
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla2/config", data)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, "02:5b:26:a8:dc:12")}
    )
    assert device is not None

    debug_info_data = debug_info.info_for_device(hass, device.id)
    assert len(debug_info_data["entities"]) == 0
    assert len(debug_info_data["triggers"]) == 2
    topic_map = {
        "homeassistant/device_automation/bla1/config": config1,
        "homeassistant/device_automation/bla2/config": config2,
    }
    assert (
        topic_map[debug_info_data["triggers"][0]["discovery_data"]["topic"]]
        != topic_map[debug_info_data["triggers"][1]["discovery_data"]["topic"]]
    )
    assert (
        debug_info_data["triggers"][0]["discovery_data"]["payload"]
        == topic_map[debug_info_data["triggers"][0]["discovery_data"]["topic"]]
    )
    assert (
        debug_info_data["triggers"][1]["discovery_data"]["payload"]
        == topic_map[debug_info_data["triggers"][1]["discovery_data"]["topic"]]
    )

    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", "")
    await hass.async_block_till_done()
    debug_info_data = debug_info.info_for_device(hass, device.id)
    assert len(debug_info_data["entities"]) == 0
    assert len(debug_info_data["triggers"]) == 1
    assert (
        debug_info_data["triggers"][0]["discovery_data"]["topic"]
        == "homeassistant/device_automation/bla2/config"
    )
    assert debug_info_data["triggers"][0]["discovery_data"]["payload"] == config2