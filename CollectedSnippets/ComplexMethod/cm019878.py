async def test_victron_battery_sensor(
    hass: HomeAssistant,
    init_integration: tuple[VictronVenusHub, MockConfigEntry],
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test SENSOR MetricKind - battery current sensor is created and updated."""
    victron_hub, mock_config_entry = init_integration

    # Inject a sensor metric (battery current)
    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/battery/0/Dc/0/Current",
        '{"value": 10.5}',
    )
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    # Verify entity was created by checking entity registry
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Exactly one entity is expected for this injected metric.
    assert len(entities) == 1
    entity = entities[0]
    assert entity.entity_id == "sensor.battery_dc_bus_current"
    assert entity.unique_id == f"{MOCK_INSTALLATION_ID}_battery_0_battery_current"
    assert entity.original_device_class is SensorDeviceClass.CURRENT
    assert entity.unit_of_measurement == "A"
    assert entity.translation_key == "battery_current"

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == "10.5"
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT
    assert state.attributes["device_class"] == "current"
    assert state.attributes["unit_of_measurement"] == "A"

    # Verify device info was registered correctly
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{MOCK_INSTALLATION_ID}_battery_0")}
    )
    assert device is not None
    assert device.manufacturer == "Victron Energy"
    assert device.name == "Battery"

    # Update the same metric to exercise the entity update callback path.
    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/battery/0/Dc/0/Current",
        '{"value": 11.2}',
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == "11.2"