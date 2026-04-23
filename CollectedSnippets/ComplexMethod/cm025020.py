async def test_restore_shared_device(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Make sure device id is stable for shared devices."""
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
        ),
    )
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry()
    config_entry_2.add_to_hass(hass)

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1-1",
        configuration_url="http://config_url_orig_1.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        entry_type=dr.DeviceEntryType.SERVICE,
        hw_version="hw_version_orig_1",
        identifiers={("entry_123", "0123")},
        manufacturer="manufacturer_orig_1",
        model="model_orig_1",
        model_id="model_id_orig_1",
        name="name_orig_1",
        serial_number="serial_no_orig_1",
        suggested_area="suggested_area_orig_1",
        sw_version="version_orig_1",
        via_device="via_device_id_orig_1",
    )

    assert len(device_registry.devices) == 1
    assert len(device_registry.deleted_devices) == 0

    # Add another config entry to the same device
    device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        configuration_url="http://config_url_orig_2.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        entry_type=None,
        hw_version="hw_version_orig_2",
        identifiers={("entry_234", "2345")},
        manufacturer="manufacturer_orig_2",
        model="model_orig_2",
        model_id="model_id_orig_2",
        name="name_orig_2",
        serial_number="serial_no_orig_2",
        suggested_area="suggested_area_orig_2",
        sw_version="version_orig_2",
        via_device="via_device_id_orig_2",
    )

    assert len(device_registry.devices) == 1
    assert len(device_registry.deleted_devices) == 0

    # Apply user customizations
    updated_device = device_registry.async_update_device(
        entry.id,
        area_id="12345A",
        disabled_by=dr.DeviceEntryDisabler.USER,
        labels={"label1", "label2"},
        name_by_user="Test Friendly Name",
    )

    # Check device entry before we remove it
    assert updated_device == dr.DeviceEntry(
        area_id="12345A",
        config_entries={config_entry_1.entry_id, config_entry_2.entry_id},
        config_entries_subentries={
            config_entry_1.entry_id: {"mock-subentry-id-1-1"},
            config_entry_2.entry_id: {None},
        },
        configuration_url="http://config_url_orig_2.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:ab:cd:ef")},
        created_at=utcnow(),
        disabled_by=dr.DeviceEntryDisabler.USER,
        entry_type=None,
        hw_version="hw_version_orig_2",
        id=entry.id,
        identifiers={("entry_123", "0123"), ("entry_234", "2345")},
        labels={"label1", "label2"},
        manufacturer="manufacturer_orig_2",
        model="model_orig_2",
        model_id="model_id_orig_2",
        modified_at=utcnow(),
        name_by_user="Test Friendly Name",
        name="name_orig_2",
        primary_config_entry=config_entry_1.entry_id,
        serial_number="serial_no_orig_2",
        suggested_area="suggested_area_orig_2",
        sw_version="version_orig_2",
    )

    device_registry.async_remove_device(entry.id)

    assert len(device_registry.devices) == 0
    assert len(device_registry.deleted_devices) == 1

    # config_entry_1 restores the original device, only the supplied config entry,
    # config subentry, connections, and identifiers will be restored, user
    # customizations of area_id, disabled_by, labels and name_by_user will be restored.
    entry2 = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1-1",
        configuration_url="http://config_url_new_1.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        entry_type=dr.DeviceEntryType.SERVICE,
        hw_version="hw_version_new_1",
        identifiers={("entry_123", "0123")},
        manufacturer="manufacturer_new_1",
        model="model_new_1",
        model_id="model_id_new_1",
        name="name_new_1",
        serial_number="serial_no_new_1",
        suggested_area="suggested_area_new_1",
        sw_version="version_new_1",
        via_device="via_device_id_new_1",
    )

    assert entry2 == dr.DeviceEntry(
        area_id="12345A",
        config_entries={config_entry_1.entry_id},
        config_entries_subentries={config_entry_1.entry_id: {"mock-subentry-id-1-1"}},
        configuration_url="http://config_url_new_1.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:ab:cd:ef")},
        created_at=utcnow(),
        disabled_by=dr.DeviceEntryDisabler.USER,
        entry_type=dr.DeviceEntryType.SERVICE,
        hw_version="hw_version_new_1",
        id=entry.id,
        identifiers={("entry_123", "0123")},
        labels={"label1", "label2"},
        manufacturer="manufacturer_new_1",
        model="model_new_1",
        model_id="model_id_new_1",
        modified_at=utcnow(),
        name_by_user="Test Friendly Name",
        name="name_new_1",
        primary_config_entry=config_entry_1.entry_id,
        serial_number="serial_no_new_1",
        suggested_area="suggested_area_new_1",
        sw_version="version_new_1",
    )

    assert len(device_registry.devices) == 1
    assert len(device_registry.deleted_devices) == 0

    assert isinstance(entry2.config_entries, set)
    assert isinstance(entry2.connections, set)
    assert isinstance(entry2.identifiers, set)

    # Remove the device again
    device_registry.async_remove_device(entry.id)

    # config_entry_2 restores the original device, only the supplied config entry,
    # config subentry, connections, and identifiers will be restored, user
    # customizations of area_id, disabled_by, labels and name_by_user will be restored.
    entry3 = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        configuration_url="http://config_url_new_2.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        entry_type=None,
        hw_version="hw_version_new_2",
        identifiers={("entry_234", "2345")},
        manufacturer="manufacturer_new_2",
        model="model_new_2",
        model_id="model_id_new_2",
        name="name_new_2",
        serial_number="serial_no_new_2",
        suggested_area="suggested_area_new_2",
        sw_version="version_new_2",
        via_device="via_device_id_new_2",
    )

    assert entry3 == dr.DeviceEntry(
        area_id="12345A",
        config_entries={config_entry_2.entry_id},
        config_entries_subentries={
            config_entry_2.entry_id: {None},
        },
        configuration_url="http://config_url_new_2.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:ab:cd:ef")},
        created_at=utcnow(),
        disabled_by=dr.DeviceEntryDisabler.USER,
        entry_type=None,
        hw_version="hw_version_new_2",
        id=entry.id,
        identifiers={("entry_234", "2345")},
        labels={"label1", "label2"},
        manufacturer="manufacturer_new_2",
        model="model_new_2",
        model_id="model_id_new_2",
        modified_at=utcnow(),
        name_by_user="Test Friendly Name",
        name="name_new_2",
        primary_config_entry=config_entry_2.entry_id,
        serial_number="serial_no_new_2",
        suggested_area="suggested_area_new_2",
        sw_version="version_new_2",
    )

    assert len(device_registry.devices) == 1
    assert len(device_registry.deleted_devices) == 0

    assert isinstance(entry3.config_entries, set)
    assert isinstance(entry3.connections, set)
    assert isinstance(entry3.identifiers, set)

    # Add config_entry_1 back to the restored device
    entry4 = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1-1",
        configuration_url="http://config_url_new_1.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        entry_type=dr.DeviceEntryType.SERVICE,
        hw_version="hw_version_new_1",
        identifiers={("entry_123", "0123")},
        manufacturer="manufacturer_new_1",
        model="model_new_1",
        model_id="model_id_new_1",
        name="name_new_1",
        serial_number="serial_no_new_1",
        suggested_area="suggested_area_new_1",
        sw_version="version_new_1",
        via_device="via_device_id_new_1",
    )

    assert entry4 == dr.DeviceEntry(
        area_id="12345A",
        config_entries={config_entry_1.entry_id, config_entry_2.entry_id},
        config_entries_subentries={
            config_entry_1.entry_id: {"mock-subentry-id-1-1"},
            config_entry_2.entry_id: {None},
        },
        configuration_url="http://config_url_new_1.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:ab:cd:ef")},
        created_at=utcnow(),
        disabled_by=dr.DeviceEntryDisabler.USER,
        entry_type=dr.DeviceEntryType.SERVICE,
        hw_version="hw_version_new_1",
        id=entry.id,
        identifiers={("entry_123", "0123"), ("entry_234", "2345")},
        labels={"label1", "label2"},
        manufacturer="manufacturer_new_1",
        model="model_new_1",
        model_id="model_id_new_1",
        modified_at=utcnow(),
        name_by_user="Test Friendly Name",
        name="name_new_1",
        primary_config_entry=config_entry_2.entry_id,
        serial_number="serial_no_new_1",
        suggested_area="suggested_area_new_1",
        sw_version="version_new_1",
    )

    assert len(device_registry.devices) == 1
    assert len(device_registry.deleted_devices) == 0

    assert isinstance(entry4.config_entries, set)
    assert isinstance(entry4.connections, set)
    assert isinstance(entry4.identifiers, set)

    await hass.async_block_till_done()

    assert len(update_events) == 8
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[1].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries": {config_entry_1.entry_id},
            "config_entries_subentries": {
                config_entry_1.entry_id: {"mock-subentry-id-1-1"}
            },
            "configuration_url": "http://config_url_orig_1.bla",
            "entry_type": dr.DeviceEntryType.SERVICE,
            "hw_version": "hw_version_orig_1",
            "identifiers": {("entry_123", "0123")},
            "manufacturer": "manufacturer_orig_1",
            "model": "model_orig_1",
            "model_id": "model_id_orig_1",
            "name": "name_orig_1",
            "serial_number": "serial_no_orig_1",
            "suggested_area": "suggested_area_orig_1",
            "sw_version": "version_orig_1",
        },
    }
    assert update_events[2].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "area_id": "suggested_area_orig_1",
            "disabled_by": None,
            "labels": set(),
            "name_by_user": None,
        },
    }
    assert update_events[3].data == {
        "action": "remove",
        "device_id": entry.id,
        "device": updated_device.dict_repr,
    }
    assert update_events[4].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[5].data == {
        "action": "remove",
        "device_id": entry.id,
        "device": entry2.dict_repr,
    }
    assert update_events[6].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[7].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries": {config_entry_2.entry_id},
            "config_entries_subentries": {config_entry_2.entry_id: {None}},
            "configuration_url": "http://config_url_new_2.bla",
            "entry_type": None,
            "hw_version": "hw_version_new_2",
            "identifiers": {("entry_234", "2345")},
            "manufacturer": "manufacturer_new_2",
            "model": "model_new_2",
            "model_id": "model_id_new_2",
            "name": "name_new_2",
            "serial_number": "serial_no_new_2",
            "suggested_area": "suggested_area_new_2",
            "sw_version": "version_new_2",
        },
    }