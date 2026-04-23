async def test_multiple_kiosk_with_empty_mac(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test that multiple kiosk devices with empty MAC don't get merged."""
    config_entry1 = MockConfigEntry(
        title="Test device 1",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "mocked-password",
            CONF_MAC: "",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
        unique_id="111111",
    )
    await _load_config(hass, config_entry1, "deviceinfo_empty_mac1.json")
    assert len(device_registry.devices) == 1

    config_entry2 = MockConfigEntry(
        title="Test device 2",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.2",
            CONF_PASSWORD: "mocked-password",
            CONF_MAC: "",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        },
        unique_id="22222",
    )
    await _load_config(hass, config_entry2, "deviceinfo_empty_mac2.json")
    assert len(device_registry.devices) == 2

    state1 = hass.states.get("sensor.test_kiosk_1_battery")
    assert state1

    state2 = hass.states.get("sensor.test_kiosk_2_battery")
    assert state2

    entry1 = entity_registry.async_get("sensor.test_kiosk_1_battery")
    assert entry1
    assert entry1.unique_id == "abcdef-111111-batteryLevel"

    entry2 = entity_registry.async_get("sensor.test_kiosk_2_battery")
    assert entry2
    assert entry2.unique_id == "abcdef-222222-batteryLevel"

    assert entry1.device_id != entry2.device_id

    device1 = device_registry.async_get(entry1.device_id)
    assert device1

    device2 = device_registry.async_get(entry2.device_id)
    assert device2

    assert device1 != device2