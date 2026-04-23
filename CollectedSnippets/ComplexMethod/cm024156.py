async def test_update_remove_triggers(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test triggers can be updated and removed."""
    await mqtt_mock_entry()
    config1 = {
        "automation_type": "trigger",
        "device": {"identifiers": ["0AFFD2"], "name": "milk"},
        "payload": "short_press",
        "topic": "foobar/triggers/button1",
        "type": "button_short_press",
        "subtype": "button_1",
    }
    config1["some_future_option_1"] = "future_option_1"
    data1 = json.dumps(config1)

    config2 = {
        "automation_type": "trigger",
        "device": {"identifiers": ["0AFFD2"], "name": "beer"},
        "payload": "short_press",
        "topic": "foobar/triggers/button1",
        "type": "button_short_press",
        "subtype": "button_1",
    }
    config2["topic"] = "foobar/tag_scanned2"
    data2 = json.dumps(config2)

    config3 = {
        "automation_type": "trigger",
        "device": {"identifiers": ["0AFFD2"], "name": "beer"},
        "payload": "short_press",
        "topic": "foobar/triggers/button1",
        "type": "button_short_press",
        "subtype": "button_2",
    }
    config3["topic"] = "foobar/tag_scanned2"
    data3 = json.dumps(config3)

    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla/config", data1)
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry.name == "milk"
    expected_triggers1: list[dict[str, Any]] = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "type": "button_short_press",
            "subtype": "button_1",
            "metadata": {},
        },
    ]
    expected_triggers2 = [dict(expected_triggers1[0])]
    expected_triggers2[0]["subtype"] = "button_2"

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == unordered(expected_triggers1)
    assert device_entry.name == "milk"

    # Update trigger topic
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla/config", data2)
    await hass.async_block_till_done()
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == unordered(expected_triggers1)
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry.name == "beer"

    # Update trigger type / subtype
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla/config", data3)
    await hass.async_block_till_done()
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == unordered(expected_triggers2)

    # Remove trigger
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla/config", "")
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry is None