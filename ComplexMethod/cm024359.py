async def test_get_triggers(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_sensor_entities: dict[str, MockSensor],
) -> None:
    """Test we get the expected triggers from a sensor."""
    setup_test_component_platform(hass, DOMAIN, mock_sensor_entities.values())
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()
    sensor_entries: dict[SensorDeviceClass, er.RegistryEntry] = {}

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    for device_class in SensorDeviceClass:
        sensor_entries[device_class] = entity_registry.async_get_or_create(
            DOMAIN,
            "test",
            mock_sensor_entities[device_class].unique_id,
            device_id=device_entry.id,
        )

    DEVICE_CLASSES_WITHOUT_TRIGGER = {
        SensorDeviceClass.DATE,
        SensorDeviceClass.ENUM,
        SensorDeviceClass.TIMESTAMP,
    }
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger["type"],
            "device_id": device_entry.id,
            "entity_id": sensor_entries[device_class].id,
            "metadata": {"secondary": False},
        }
        for device_class in SensorDeviceClass
        if device_class in UNITS_OF_MEASUREMENT
        and device_class not in DEVICE_CLASSES_WITHOUT_TRIGGER
        for trigger in ENTITY_TRIGGERS[device_class]
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert len(triggers) == 57
    assert triggers == unordered(expected_triggers)