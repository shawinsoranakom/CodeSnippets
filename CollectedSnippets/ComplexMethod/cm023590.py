async def test_if_fires_on_mqtt_message_swc(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    service_calls: list[ServiceCall],
    mqtt_mock: MqttMockHAClient,
    setup_tasmota,
) -> None:
    """Test switch triggers firing."""
    # Discover a device with 2 device triggers
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    config["swc"][1] = 0
    config["swc"][2] = 9
    config["swn"][2] = "custom_switch"
    mac = config["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
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
                        "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press_1")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_2_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_2",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press_2")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_3_HOLD",
                        "subtype": "switch_3",
                        "type": "button_double_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("long_press_3")},
                    },
                },
            ]
        },
    )

    # Fake switch 1 short press.
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "short_press_1"

    # Fake switch 2 short press.
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch2":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "short_press_2"

    # Fake switch 3 long press.
    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"custom_switch":{"Action":"HOLD"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "long_press_3"