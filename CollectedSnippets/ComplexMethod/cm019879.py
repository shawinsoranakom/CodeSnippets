async def test_victron_time(
    hass: HomeAssistant,
    init_integration: tuple[VictronVenusHub, MockConfigEntry],
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test TIME MetricKind - ESS schedule charge start time is created and updated."""
    victron_hub, mock_config_entry = init_integration

    # 480 raw seconds, library converts to 8 minutes -> time(0, 8)
    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/0/Start",
        '{"value": 480}',
    )
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    assert len(entities) == 1
    entity = entities[0]
    assert (
        entity.entity_id == "time.victron_venus_ess_batterylife_schedule_charge_0_start"
    )
    assert (
        entity.unique_id
        == f"{MOCK_INSTALLATION_ID}_system_0_system_ess_schedule_charge_0_start"
    )
    assert entity.translation_key == "system_ess_schedule_charge_slot_start"

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == "00:08:00"

    # Verify device info was registered correctly
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{MOCK_INSTALLATION_ID}_system_0")}
    )
    assert device is not None
    assert device.manufacturer == "Victron Energy"

    # Update: 3600 raw seconds, library converts to 60 minutes -> time(1, 0)
    await inject_message(
        victron_hub,
        f"N/{MOCK_INSTALLATION_ID}/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/0/Start",
        '{"value": 3600}',
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state == "01:00:00"