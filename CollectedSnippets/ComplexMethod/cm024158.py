async def test_if_fires_on_mqtt_message_after_update(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    service_calls: list[ServiceCall],
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test triggers firing after update."""
    await mqtt_mock_entry()
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    data2 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "button_short_press",'
        '  "subtype": "button_2" }'
    )
    data3 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"]},'
        '  "topic": "foobar/triggers/buttonOne",'
        '  "type": "button_short_press",'
        '  "subtype": "button_1" }'
    )
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", data1)
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla2/config", data2)
    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "bla1",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()

    # Fake short press.
    async_fire_mqtt_message(hass, "foobar/triggers/button1", "")
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    # Update the trigger with existing type/subtype change
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla2/config", data1)
    await hass.async_block_till_done()
    assert "Cannot update device trigger ('device_automation', 'bla2')" in caplog.text

    # Update the trigger with different topic
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", data3)
    await hass.async_block_till_done()

    service_calls.clear()
    async_fire_mqtt_message(hass, "foobar/triggers/button1", "")
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    service_calls.clear()
    async_fire_mqtt_message(hass, "foobar/triggers/buttonOne", "")
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    # Update the trigger with same topic
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", data3)
    await hass.async_block_till_done()

    service_calls.clear()
    async_fire_mqtt_message(hass, "foobar/triggers/button1", "")
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    service_calls.clear()
    async_fire_mqtt_message(hass, "foobar/triggers/buttonOne", "")
    await hass.async_block_till_done()
    assert len(service_calls) == 1