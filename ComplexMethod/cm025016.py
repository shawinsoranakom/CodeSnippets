async def test_update_remove_config_entry_disabled_by(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    removed_config_entry_disabled_by: config_entries.ConfigEntryDisabler | None,
    device_disabled_by_initial: dr.DeviceEntryDisabler | None,
    device_disabled_by_updated: dr.DeviceEntryDisabler | None,
    extra_changes: dict[str, Any],
) -> None:
    """Check how the disabled_by flag is treated when removing a config entry."""
    config_entry_1 = MockConfigEntry(
        title=None, disabled_by=removed_config_entry_disabled_by
    )
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry(
        title=None, disabled_by=config_entries.ConfigEntryDisabler.USER
    )
    config_entry_2.add_to_hass(hass)
    update_events = async_capture_events(hass, dr.EVENT_DEVICE_REGISTRY_UPDATED)
    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id=None,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        disabled_by=device_disabled_by_initial,
    )
    assert entry.disabled_by == device_disabled_by_initial

    entry2 = device_registry.async_update_device(
        entry.id, add_config_entry_id=config_entry_2.entry_id
    )
    assert entry2.disabled_by == device_disabled_by_initial

    entry3 = device_registry.async_update_device(
        entry.id, remove_config_entry_id=config_entry_1.entry_id
    )

    assert entry3 == dr.DeviceEntry(
        config_entries={config_entry_2.entry_id},
        config_entries_subentries={config_entry_2.entry_id: {None}},
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:ab:cd:ef")},
        created_at=utcnow(),
        disabled_by=device_disabled_by_updated,
        id=entry.id,
        modified_at=utcnow(),
        primary_config_entry=None,
    )

    await hass.async_block_till_done()

    assert len(update_events) == 3
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[1].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries": {config_entry_1.entry_id},
            "config_entries_subentries": {config_entry_1.entry_id: {None}},
        },
    }
    assert update_events[2].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries": {config_entry_1.entry_id, config_entry_2.entry_id},
            "config_entries_subentries": {
                config_entry_1.entry_id: {None},
                config_entry_2.entry_id: {None},
            },
        }
        | extra_changes,
    }