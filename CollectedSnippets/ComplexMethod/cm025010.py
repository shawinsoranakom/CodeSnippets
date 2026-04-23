async def test_deleted_device_removing_config_subentries(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Make sure we do not get duplicate entries."""
    update_events = async_capture_events(hass, dr.EVENT_DEVICE_REGISTRY_UPDATED)
    config_entry_1 = MockConfigEntry(
        subentries_data=(
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1-2",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        )
    )
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry(
        subentries_data=(
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-2-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        )
    )
    config_entry_2.add_to_hass(hass)

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry2 = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1-1",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry3 = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1-2",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry4 = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        config_subentry_id="mock-subentry-id-2-1",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "4567")},
        manufacturer="manufacturer",
        model="model",
    )

    assert len(device_registry.devices) == 1
    assert len(device_registry.deleted_devices) == 0
    assert entry.id == entry2.id
    assert entry.id == entry3.id
    assert entry.id == entry4.id
    assert entry4.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry4.config_entries_subentries == {
        config_entry_1.entry_id: {None, "mock-subentry-id-1-1", "mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
    }

    device_registry.async_remove_device(entry.id)

    assert len(device_registry.devices) == 0
    assert len(device_registry.deleted_devices) == 1

    await hass.async_block_till_done()

    assert len(update_events) == 5
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[1].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries_subentries": {config_entry_1.entry_id: {None}},
        },
    }
    assert update_events[2].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries_subentries": {
                config_entry_1.entry_id: {None, "mock-subentry-id-1-1"}
            },
        },
    }
    assert update_events[3].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries": {config_entry_1.entry_id},
            "config_entries_subentries": {
                config_entry_1.entry_id: {
                    None,
                    "mock-subentry-id-1-1",
                    "mock-subentry-id-1-2",
                }
            },
            "identifiers": {("bridgeid", "0123")},
        },
    }
    assert update_events[4].data == {
        "action": "remove",
        "device_id": entry.id,
        "device": entry4.dict_repr,
    }

    device_registry.async_clear_config_subentry(config_entry_1.entry_id, None)
    entry = device_registry.deleted_devices.get_entry({("bridgeid", "0123")}, None)
    assert entry.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-1", "mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
    }
    assert entry.orphaned_timestamp is None

    hass.config_entries.async_remove_subentry(config_entry_1, "mock-subentry-id-1-1")
    entry = device_registry.deleted_devices.get_entry({("bridgeid", "0123")}, None)
    assert entry.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
    }
    assert entry.orphaned_timestamp is None

    # Remove the same subentry again
    device_registry.async_clear_config_subentry(
        config_entry_1.entry_id, "mock-subentry-id-1-1"
    )
    assert (
        device_registry.deleted_devices.get_entry({("bridgeid", "0123")}, None) is entry
    )

    hass.config_entries.async_remove_subentry(config_entry_1, "mock-subentry-id-1-2")
    entry = device_registry.deleted_devices.get_entry({("bridgeid", "0123")}, None)
    assert entry.config_entries == {config_entry_2.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_2.entry_id: {"mock-subentry-id-2-1"}
    }
    assert entry.orphaned_timestamp is None

    hass.config_entries.async_remove_subentry(config_entry_2, "mock-subentry-id-2-1")
    entry = device_registry.deleted_devices.get_entry({("bridgeid", "0123")}, None)
    assert entry.config_entries == set()
    assert entry.config_entries_subentries == {}
    assert entry.orphaned_timestamp is not None

    # No event when a deleted device is purged
    await hass.async_block_till_done()
    assert len(update_events) == 5

    # Re-add, expect to keep the device id
    hass.config_entries.async_add_subentry(
        config_entry_2,
        config_entries.ConfigSubentry(
            data={},
            subentry_id="mock-subentry-id-2-1",
            subentry_type="test",
            title="Mock title",
            unique_id="test",
        ),
    )
    restored_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        config_subentry_id="mock-subentry-id-2-1",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    assert restored_entry.id == entry.id

    # Remove again, and trigger purge
    device_registry.async_remove_device(entry.id)
    hass.config_entries.async_remove_subentry(config_entry_2, "mock-subentry-id-2-1")
    entry = device_registry.deleted_devices.get_entry({("bridgeid", "0123")}, None)
    assert entry.config_entries == set()
    assert entry.config_entries_subentries == {}
    assert entry.orphaned_timestamp is not None

    future_time = time.time() + dr.ORPHANED_DEVICE_KEEP_SECONDS + 1

    with patch("time.time", return_value=future_time):
        device_registry.async_purge_expired_orphaned_devices()

    assert len(device_registry.devices) == 0
    assert len(device_registry.deleted_devices) == 0

    # Re-add, expect to get a new device id after the purge
    new_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    assert new_entry.id != entry.id