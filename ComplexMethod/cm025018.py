async def test_restore_migrated_device_disabled_by(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
    device_disabled_by: dr.DeviceEntryDisabler | UndefinedType | None,
    expected_disabled_by: dr.DeviceEntryDisabler | None,
) -> None:
    """Check how the disabled_by flag is treated when restoring a device."""
    entry_id = mock_config_entry.entry_id
    update_events = async_capture_events(hass, dr.EVENT_DEVICE_REGISTRY_UPDATED)
    entry = device_registry.async_get_or_create(
        config_entry_id=entry_id,
        config_subentry_id=None,
        configuration_url="http://config_url_orig.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        disabled_by=None,
        entry_type=dr.DeviceEntryType.SERVICE,
        hw_version="hw_version_orig",
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer_orig",
        model="model_orig",
        model_id="model_id_orig",
        name="name_orig",
        serial_number="serial_no_orig",
        suggested_area="suggested_area_orig",
        sw_version="version_orig",
        via_device="via_device_id_orig",
    )

    assert len(device_registry.devices) == 1
    assert len(device_registry.deleted_devices) == 0

    device_registry.async_remove_device(entry.id)

    assert len(device_registry.devices) == 0
    assert len(device_registry.deleted_devices) == 1

    deleted_entry = device_registry.deleted_devices[entry.id]
    device_registry.deleted_devices[entry.id] = attr.evolve(
        deleted_entry, disabled_by=UNDEFINED
    )

    # This will restore the original device, user customizations of
    # area_id, disabled_by, labels and name_by_user will be restored
    entry3 = device_registry.async_get_or_create(
        config_entry_id=entry_id,
        config_subentry_id=None,
        configuration_url="http://config_url_new.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        disabled_by=device_disabled_by,
        entry_type=None,
        hw_version="hw_version_new",
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer_new",
        model="model_new",
        model_id="model_id_new",
        name="name_new",
        serial_number="serial_no_new",
        suggested_area="suggested_area_new",
        sw_version="version_new",
        via_device="via_device_id_new",
    )
    assert entry3 == dr.DeviceEntry(
        area_id="suggested_area_orig",
        config_entries={entry_id},
        config_entries_subentries={entry_id: {None}},
        configuration_url="http://config_url_new.bla",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:ab:cd:ef")},
        created_at=utcnow(),
        disabled_by=expected_disabled_by,
        entry_type=None,
        hw_version="hw_version_new",
        id=entry.id,
        identifiers={("bridgeid", "0123")},
        labels=set(),
        manufacturer="manufacturer_new",
        model="model_new",
        model_id="model_id_new",
        modified_at=utcnow(),
        name_by_user=None,
        name="name_new",
        primary_config_entry=entry_id,
        serial_number="serial_no_new",
        suggested_area="suggested_area_new",
        sw_version="version_new",
    )

    assert entry.id == entry3.id
    assert len(device_registry.devices) == 1
    assert len(device_registry.deleted_devices) == 0

    assert isinstance(entry3.config_entries, set)
    assert isinstance(entry3.connections, set)
    assert isinstance(entry3.identifiers, set)

    await hass.async_block_till_done()

    assert len(update_events) == 3
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[1].data == {
        "action": "remove",
        "device_id": entry.id,
        "device": entry.dict_repr,
    }
    assert update_events[2].data == {
        "action": "create",
        "device_id": entry3.id,
    }