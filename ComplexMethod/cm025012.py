async def test_update(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Verify that we can update some attributes of a device."""
    created_at = datetime.fromisoformat("2024-01-01T01:00:00+00:00")
    freezer.move_to(created_at)
    update_events = async_capture_events(hass, dr.EVENT_DEVICE_REGISTRY_UPDATED)
    entry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("hue", "456"), ("bla", "123")},
    )
    new_connections = {(dr.CONNECTION_NETWORK_MAC, "65:43:21:FE:DC:BA")}
    new_identifiers = {("hue", "654"), ("bla", "321")}
    assert not entry.area_id
    assert not entry.labels
    assert not entry.name_by_user
    assert entry.created_at == created_at
    assert entry.modified_at == created_at

    modified_at = datetime.fromisoformat("2024-02-01T01:00:00+00:00")
    freezer.move_to(modified_at)
    with patch.object(device_registry, "async_schedule_save") as mock_save:
        updated_entry = device_registry.async_update_device(
            entry.id,
            area_id="12345A",
            configuration_url="https://example.com/config",
            disabled_by=dr.DeviceEntryDisabler.USER,
            entry_type=dr.DeviceEntryType.SERVICE,
            hw_version="hw_version",
            labels={"label1", "label2"},
            manufacturer="Test Producer",
            model="Test Model",
            model_id="Test Model Name",
            name_by_user="Test Friendly Name",
            name="name",
            new_connections=new_connections,
            new_identifiers=new_identifiers,
            serial_number="serial_no",
            suggested_area="suggested_area",
            sw_version="version",
            via_device_id="98765B",
        )

    assert mock_save.call_count == 1
    assert updated_entry != entry
    assert updated_entry == dr.DeviceEntry(
        area_id="12345A",
        config_entries={mock_config_entry.entry_id},
        config_entries_subentries={mock_config_entry.entry_id: {None}},
        configuration_url="https://example.com/config",
        connections={("mac", "65:43:21:fe:dc:ba")},
        created_at=created_at,
        disabled_by=dr.DeviceEntryDisabler.USER,
        entry_type=dr.DeviceEntryType.SERVICE,
        hw_version="hw_version",
        id=entry.id,
        identifiers={("bla", "321"), ("hue", "654")},
        labels={"label1", "label2"},
        manufacturer="Test Producer",
        model="Test Model",
        model_id="Test Model Name",
        modified_at=modified_at,
        name_by_user="Test Friendly Name",
        name="name",
        serial_number="serial_no",
        suggested_area="suggested_area",
        sw_version="version",
        via_device_id="98765B",
    )

    assert device_registry.async_get_device(identifiers={("hue", "456")}) is None
    assert device_registry.async_get_device(identifiers={("bla", "123")}) is None

    assert (
        device_registry.async_get_device(identifiers={("hue", "654")}) == updated_entry
    )
    assert (
        device_registry.async_get_device(identifiers={("bla", "321")}) == updated_entry
    )

    assert (
        device_registry.async_get_device(
            connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")}
        )
        is None
    )
    assert (
        device_registry.async_get_device(
            connections={(dr.CONNECTION_NETWORK_MAC, "65:43:21:FE:DC:BA")}
        )
        == updated_entry
    )

    assert device_registry.async_get(updated_entry.id) is not None

    await hass.async_block_till_done()

    assert len(update_events) == 2
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry.id,
    }
    assert update_events[1].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "area_id": None,
            "connections": {("mac", "12:34:56:ab:cd:ef")},
            "configuration_url": None,
            "disabled_by": None,
            "entry_type": None,
            "hw_version": None,
            "identifiers": {("bla", "123"), ("hue", "456")},
            "labels": set(),
            "manufacturer": None,
            "model": None,
            "model_id": None,
            "name": None,
            "name_by_user": None,
            "serial_number": None,
            "suggested_area": None,
            "sw_version": None,
            "via_device_id": None,
        },
    }
    with pytest.raises(HomeAssistantError):
        device_registry.async_update_device(
            entry.id,
            merge_connections=new_connections,
            new_connections=new_connections,
        )

    with pytest.raises(HomeAssistantError):
        device_registry.async_update_device(
            entry.id,
            merge_identifiers=new_identifiers,
            new_identifiers=new_identifiers,
        )