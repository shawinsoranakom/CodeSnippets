async def test_deleted_device_removing_config_entries(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Make sure we do not get duplicate entries."""
    update_events = async_capture_events(hass, dr.EVENT_DEVICE_REGISTRY_UPDATED)
    config_entry_1 = MockConfigEntry()
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry()
    config_entry_2.add_to_hass(hass)

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry2 = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry3 = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "34:56:78:CD:EF:12")},
        identifiers={("bridgeid", "4567")},
        manufacturer="manufacturer",
        model="model",
    )

    assert len(device_registry.devices) == 2
    assert len(device_registry.deleted_devices) == 0
    assert entry.id == entry2.id
    assert entry.id != entry3.id
    assert entry2.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry2.config_entries_subentries == {
        config_entry_1.entry_id: {None},
        config_entry_2.entry_id: {None},
    }

    device_registry.async_remove_device(entry.id)
    device_registry.async_remove_device(entry3.id)

    assert len(device_registry.devices) == 0
    assert len(device_registry.deleted_devices) == 2

    await hass.async_block_till_done()
    assert len(update_events) == 5
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[1].data == {
        "action": "update",
        "device_id": entry2.id,
        "changes": {
            "config_entries": {config_entry_1.entry_id},
            "config_entries_subentries": {config_entry_1.entry_id: {None}},
        },
    }
    assert update_events[2].data == {
        "action": "create",
        "device_id": entry3.id,
    }
    assert update_events[3].data == {
        "action": "remove",
        "device_id": entry.id,
        "device": entry2.dict_repr,
    }
    assert update_events[4].data == {
        "action": "remove",
        "device_id": entry3.id,
        "device": entry3.dict_repr,
    }

    device_registry.async_clear_config_entry(config_entry_1.entry_id)
    assert len(device_registry.devices) == 0
    assert len(device_registry.deleted_devices) == 2
    entry = device_registry.deleted_devices.get_entry({("bridgeid", "0123")}, None)
    assert entry.config_entries == {config_entry_2.entry_id}
    assert entry.config_entries_subentries == {config_entry_2.entry_id: {None}}

    device_registry.async_clear_config_entry(config_entry_2.entry_id)
    assert len(device_registry.devices) == 0
    assert len(device_registry.deleted_devices) == 2
    entry = device_registry.deleted_devices.get_entry({("bridgeid", "0123")}, None)
    assert entry.config_entries == set()
    assert entry.config_entries_subentries == {}

    # No event when a deleted device is purged
    await hass.async_block_till_done()
    assert len(update_events) == 5

    # Re-add, expect to keep the device id
    entry2 = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )

    assert entry.id == entry2.id

    future_time = time.time() + dr.ORPHANED_DEVICE_KEEP_SECONDS + 1

    with patch("time.time", return_value=future_time):
        device_registry.async_purge_expired_orphaned_devices()

    # Re-add, expect to get a new device id after the purge
    entry4 = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    assert entry3.id != entry4.id