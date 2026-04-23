async def test_victron_number_with_step(
    hass: HomeAssistant,
    init_integration: tuple[VictronVenusHub, MockConfigEntry],
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test NUMBER entity with a metric that has a numeric step value."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/settings/0/Settings/SystemSetup/MaxChargeVoltage",
        '{"value": 57.6}',
    )
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entities) == 1
    entity = entities[0]
    assert entity.entity_id == "number.victron_venus_ess_max_charge_voltage"
    assert (
        entity.unique_id
        == f"{MOCK_INSTALLATION_ID}_system_0_system_ess_max_charge_voltage"
    )
    assert entity.original_device_class is NumberDeviceClass.VOLTAGE
    assert entity.unit_of_measurement == "V"
    assert entity.translation_key == "system_ess_max_charge_voltage"

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == "57.6"
    assert state.attributes["device_class"] == "voltage"
    assert state.attributes["unit_of_measurement"] == "V"
    assert state.attributes["step"] == 0.1
    assert state.attributes["min"] == 0.0
    assert state.attributes["max"] == 100.0

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{MOCK_INSTALLATION_ID}_system_0")}
    )
    assert device is not None
    assert device.manufacturer == "Victron Energy"