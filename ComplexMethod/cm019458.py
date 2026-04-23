async def test_devices_creaction_ok(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    local_oauth_impl: ClientSession,
    mock_get_devices_twolightswitches,
    mock_get_status_filled,
    snapshot: SnapshotAssertion,
) -> None:
    """Test iotty switch creation."""

    entity_id = "switch.test_light_switch_0_test_serial_0"

    mock_config_entry.add_to_hass(hass)

    config_entry_oauth2_flow.async_register_implementation(
        hass, DOMAIN, local_oauth_impl
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert (state := hass.states.get(entity_id))
    assert state == snapshot(name="state")

    assert (entry := entity_registry.async_get(entity_id))
    assert entry == snapshot(name="entity")

    assert entry.device_id
    assert (device_entry := device_registry.async_get(entry.device_id))
    assert device_entry == snapshot(name="device")

    assert hass.states.async_entity_ids_count() == 2
    assert hass.states.async_entity_ids() == snapshot(name="entity-ids")