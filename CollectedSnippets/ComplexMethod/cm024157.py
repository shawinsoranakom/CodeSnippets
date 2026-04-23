async def test_non_unique_triggers(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    service_calls: list[ServiceCall],
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test non unique triggers."""
    await mqtt_mock_entry()
    data1 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"], "name": "milk"},'
        '  "payload": "short_press",'
        '  "topic": "foobar/triggers/button1",'
        '  "type": "press",'
        '  "subtype": "button" }'
    )
    data2 = (
        '{ "automation_type":"trigger",'
        '  "device":{"identifiers":["0AFFD2"], "name": "beer"},'
        '  "payload": "long_press",'
        '  "topic": "foobar/triggers/button2",'
        '  "type": "press",'
        '  "subtype": "button" }'
    )
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", data1)
    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    assert device_entry.name == "milk"

    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla2/config", data2)
    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(identifiers={("mqtt", "0AFFD2")})
    # The device entry was updated, but the trigger was not unique
    # and therefore it was not set up.
    assert device_entry.name == "beer"
    assert (
        "Config for device trigger bla2 conflicts with existing device trigger, cannot set up trigger"
        in caplog.text
    )

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
                        "type": "press",
                        "subtype": "button",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("press1")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "type": "press",
                        "subtype": "button",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("press2")},
                    },
                },
            ]
        },
    )

    # Try to trigger first config.
    # and triggers both attached instances.
    async_fire_mqtt_message(hass, "foobar/triggers/button1", "short_press")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    all_calls = {service_calls[0].data["some"], service_calls[1].data["some"]}
    assert all_calls == {"press1", "press2"}

    # Trigger second config references to same trigger
    # and triggers both attached instances.
    async_fire_mqtt_message(hass, "foobar/triggers/button2", "long_press")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    all_calls = {service_calls[0].data["some"], service_calls[1].data["some"]}
    assert all_calls == {"press1", "press2"}

    # Removing the first trigger will clean up
    service_calls.clear()
    async_fire_mqtt_message(hass, "homeassistant/device_automation/bla1/config", "")
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    assert (
        "Device trigger ('device_automation', 'bla1') has been removed" in caplog.text
    )
    async_fire_mqtt_message(hass, "foobar/triggers/button1", "short_press")
    assert len(service_calls) == 0