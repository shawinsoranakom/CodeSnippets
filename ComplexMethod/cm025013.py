async def test_update_remove_config_entries(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Make sure we do not get duplicate entries."""
    update_events = async_capture_events(hass, dr.EVENT_DEVICE_REGISTRY_UPDATED)
    config_entry_1 = MockConfigEntry()
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry()
    config_entry_2.add_to_hass(hass)
    config_entry_3 = MockConfigEntry()
    config_entry_3.add_to_hass(hass)

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
    entry4 = device_registry.async_update_device(
        entry2.id, add_config_entry_id=config_entry_3.entry_id
    )
    # Try to add an unknown config entry
    with pytest.raises(HomeAssistantError):
        device_registry.async_update_device(entry2.id, add_config_entry_id="blabla")

    assert len(device_registry.devices) == 2
    assert entry.id == entry2.id == entry4.id
    assert entry.id != entry3.id
    assert entry2.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry4.config_entries == {
        config_entry_1.entry_id,
        config_entry_2.entry_id,
        config_entry_3.entry_id,
    }

    device_registry.async_update_device(
        entry2.id, remove_config_entry_id=config_entry_1.entry_id
    )
    updated_entry = device_registry.async_update_device(
        entry2.id, remove_config_entry_id=config_entry_3.entry_id
    )
    removed_entry = device_registry.async_update_device(
        entry3.id, remove_config_entry_id=config_entry_1.entry_id
    )

    assert updated_entry.config_entries == {config_entry_2.entry_id}
    assert removed_entry is None

    removed_entry = device_registry.async_get_device(identifiers={("bridgeid", "4567")})

    assert removed_entry is None

    await hass.async_block_till_done()

    assert len(update_events) == 7
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
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries": {config_entry_1.entry_id, config_entry_2.entry_id},
            "config_entries_subentries": {
                config_entry_1.entry_id: {None},
                config_entry_2.entry_id: {None},
            },
        },
    }
    assert update_events[4].data == {
        "action": "update",
        "device_id": entry2.id,
        "changes": {
            "config_entries": {
                config_entry_1.entry_id,
                config_entry_2.entry_id,
                config_entry_3.entry_id,
            },
            "config_entries_subentries": {
                config_entry_1.entry_id: {None},
                config_entry_2.entry_id: {None},
                config_entry_3.entry_id: {None},
            },
            "primary_config_entry": config_entry_1.entry_id,
        },
    }
    assert update_events[5].data == {
        "action": "update",
        "device_id": entry2.id,
        "changes": {
            "config_entries": {config_entry_2.entry_id, config_entry_3.entry_id},
            "config_entries_subentries": {
                config_entry_2.entry_id: {None},
                config_entry_3.entry_id: {None},
            },
        },
    }
    assert update_events[6].data == {
        "action": "remove",
        "device_id": entry3.id,
        "device": entry3.dict_repr,
    }