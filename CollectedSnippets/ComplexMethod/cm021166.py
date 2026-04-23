async def test_button_snapshot(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Snapshot the button entity (registry + state)."""
    await snapshot_platform(
        hass,
        entity_registry,
        snapshot,
        mock_config_entry.entry_id,
    )

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entity_entries) == 2

    # Check Reboot button is associated with the gateway device
    reboot_entry = next(
        e for e in entity_entries if e.entity_id == "button.klf_200_gateway_restart"
    )
    assert reboot_entry.device_id is not None
    gateway_device = device_registry.async_get(reboot_entry.device_id)
    assert gateway_device is not None
    assert (
        DOMAIN,
        f"gateway_{mock_config_entry.entry_id}",
    ) in gateway_device.identifiers
    assert gateway_device.via_device_id is None

    # Check Identify button is associated with the node device via the gateway
    identify_entry = next(
        e for e in entity_entries if e.entity_id == "button.test_window_identify"
    )
    assert identify_entry.device_id is not None
    node_device = device_registry.async_get(identify_entry.device_id)
    assert node_device is not None
    assert (DOMAIN, "123456789") in node_device.identifiers
    assert node_device.via_device_id == gateway_device.id