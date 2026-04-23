async def test_cleanup_device_several_triggers(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test removal from device registry when the last trigger is removed."""
    await mqtt_mock_entry()
    config1 = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo",
        "subtype": "bar",
        "device": {"identifiers": ["helloworld"]},
    }

    config2 = {
        "automation_type": "trigger",
        "topic": "test-topic",
        "type": "foo2",
        "subtype": "bar",
        "device": {"identifiers": ["helloworld"]},
    }

    data1 = json.dumps(config1)
    data2 = json.dumps(config2)
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", data1)
    await hass.async_block_till_done()
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla2/config", data2)
    await hass.async_block_till_done()

    # Verify device registry entry is created
    device_entry = device_registry.async_get_device(
        identifiers={("mqtt", "helloworld")}
    )
    assert device_entry is not None

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert len(triggers) == 2
    assert triggers[0]["type"] == "foo"
    assert triggers[1]["type"] == "foo2"

    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", "")
    await hass.async_block_till_done()

    # Verify device registry entry is not cleared
    device_entry = device_registry.async_get_device(
        identifiers={("mqtt", "helloworld")}
    )
    assert device_entry is not None

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert len(triggers) == 1
    assert triggers[0]["type"] == "foo2"

    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla2/config", "")
    await hass.async_block_till_done()

    # Verify device registry entry is cleared
    device_entry = device_registry.async_get_device(
        identifiers={("mqtt", "helloworld")}
    )
    assert device_entry is None