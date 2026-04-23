async def test_loading_from_storage(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test loading stored devices on start."""
    created_at = "2024-01-01T00:00:00+00:00"
    modified_at = "2024-02-01T00:00:00+00:00"
    hass_storage[dr.STORAGE_KEY] = {
        "version": dr.STORAGE_VERSION_MAJOR,
        "minor_version": dr.STORAGE_VERSION_MINOR,
        "data": {
            "devices": [
                {
                    "area_id": "12345A",
                    "config_entries": [mock_config_entry.entry_id],
                    "config_entries_subentries": {mock_config_entry.entry_id: [None]},
                    "configuration_url": "https://example.com/config",
                    "connections": [["Zigbee", "01.23.45.67.89"]],
                    "created_at": created_at,
                    "disabled_by": dr.DeviceEntryDisabler.USER,
                    "entry_type": dr.DeviceEntryType.SERVICE,
                    "hw_version": "hw_version",
                    "id": "abcdefghijklm",
                    "identifiers": [["serial", "123456ABCDEF"]],
                    "labels": {"label1", "label2"},
                    "manufacturer": "manufacturer",
                    "model": "model",
                    "model_id": "model_id",
                    "modified_at": modified_at,
                    "name_by_user": "Test Friendly Name",
                    "name": "name",
                    "primary_config_entry": mock_config_entry.entry_id,
                    "serial_number": "serial_no",
                    "sw_version": "version",
                    "via_device_id": None,
                }
            ],
            "deleted_devices": [
                {
                    "area_id": "12345A",
                    "config_entries": [mock_config_entry.entry_id],
                    "config_entries_subentries": {mock_config_entry.entry_id: [None]},
                    "connections": [["Zigbee", "23.45.67.89.01"]],
                    "created_at": created_at,
                    "disabled_by": dr.DeviceEntryDisabler.USER,
                    "disabled_by_undefined": False,
                    "id": "bcdefghijklmn",
                    "identifiers": [["serial", "3456ABCDEF12"]],
                    "labels": {"label1", "label2"},
                    "modified_at": modified_at,
                    "name_by_user": "Test Friendly Name",
                    "orphaned_timestamp": None,
                }
            ],
        },
    }

    dr.async_setup(hass)
    await dr.async_load(hass)
    registry = dr.async_get(hass)
    assert len(registry.devices) == 1
    assert len(registry.deleted_devices) == 1

    assert registry.deleted_devices["bcdefghijklmn"] == dr.DeletedDeviceEntry(
        area_id="12345A",
        config_entries={mock_config_entry.entry_id},
        config_entries_subentries={mock_config_entry.entry_id: {None}},
        connections={("Zigbee", "23.45.67.89.01")},
        created_at=datetime.fromisoformat(created_at),
        disabled_by=dr.DeviceEntryDisabler.USER,
        id="bcdefghijklmn",
        identifiers={("serial", "3456ABCDEF12")},
        labels={"label1", "label2"},
        modified_at=datetime.fromisoformat(modified_at),
        name_by_user="Test Friendly Name",
        orphaned_timestamp=None,
    )

    entry = registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={("Zigbee", "01.23.45.67.89")},
        identifiers={("serial", "123456ABCDEF")},
        manufacturer="manufacturer",
        model="model",
    )
    assert entry == dr.DeviceEntry(
        area_id="12345A",
        config_entries={mock_config_entry.entry_id},
        config_entries_subentries={mock_config_entry.entry_id: {None}},
        configuration_url="https://example.com/config",
        connections={("Zigbee", "01.23.45.67.89")},
        created_at=datetime.fromisoformat(created_at),
        disabled_by=dr.DeviceEntryDisabler.USER,
        entry_type=dr.DeviceEntryType.SERVICE,
        hw_version="hw_version",
        id="abcdefghijklm",
        identifiers={("serial", "123456ABCDEF")},
        labels={"label1", "label2"},
        manufacturer="manufacturer",
        model="model",
        model_id="model_id",
        modified_at=datetime.fromisoformat(modified_at),
        name_by_user="Test Friendly Name",
        name="name",
        primary_config_entry=mock_config_entry.entry_id,
        serial_number="serial_no",
        sw_version="version",
    )
    assert isinstance(entry.config_entries, set)
    assert isinstance(entry.connections, set)
    assert isinstance(entry.identifiers, set)

    # Restore a device, id should be reused from the deleted device entry
    entry = registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={("Zigbee", "23.45.67.89.01")},
        identifiers={("serial", "3456ABCDEF12")},
        manufacturer="manufacturer",
        model="model",
    )
    assert entry == dr.DeviceEntry(
        area_id="12345A",
        config_entries={mock_config_entry.entry_id},
        config_entries_subentries={mock_config_entry.entry_id: {None}},
        connections={("Zigbee", "23.45.67.89.01")},
        created_at=datetime.fromisoformat(created_at),
        disabled_by=dr.DeviceEntryDisabler.USER,
        id="bcdefghijklmn",
        identifiers={("serial", "3456ABCDEF12")},
        labels={"label1", "label2"},
        manufacturer="manufacturer",
        model="model",
        modified_at=utcnow(),
        name_by_user="Test Friendly Name",
        primary_config_entry=mock_config_entry.entry_id,
    )
    assert entry.id == "bcdefghijklmn"
    assert isinstance(entry.config_entries, set)
    assert isinstance(entry.connections, set)
    assert isinstance(entry.identifiers, set)