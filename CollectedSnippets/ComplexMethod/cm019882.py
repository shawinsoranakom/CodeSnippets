async def test_victron_switch(
    hass: HomeAssistant,
    init_integration: tuple[VictronVenusHub, MockConfigEntry],
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test SWITCH MetricKind - EV charger charge switch is created and updated."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/evcharger/0/StartStop",
        '{"value": 1}',
    )
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    assert len(entities) == 1
    entity = entities[0]
    assert entity.entity_id == "switch.ev_charging_station_ev_charging"
    assert entity.unique_id == f"{MOCK_INSTALLATION_ID}_evcharger_0_evcharger_charge"
    assert entity.translation_key == "evcharger_charge"

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == BINARY_SENSOR_ON_ID

    # Verify device info was registered correctly
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{MOCK_INSTALLATION_ID}_evcharger_0")}
    )
    assert device is not None
    assert device.manufacturer == "Victron Energy"

    # Update the metric to exercise the entity update callback path.
    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/evcharger/0/StartStop",
        '{"value": 0}',
    )
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == BINARY_SENSOR_OFF_ID