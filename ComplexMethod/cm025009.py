async def test_removing_config_subentries(
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
    assert entry.id == entry2.id
    assert entry.id == entry3.id
    assert entry.id == entry4.id
    assert entry4.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry4.config_entries_subentries == {
        config_entry_1.entry_id: {None, "mock-subentry-id-1-1", "mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
    }

    device_registry.async_update_device(
        entry.id,
        remove_config_entry_id=config_entry_1.entry_id,
        remove_config_subentry_id=None,
    )
    entry = device_registry.async_get_device(identifiers={("bridgeid", "0123")})
    assert entry.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-1", "mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
    }

    hass.config_entries.async_remove_subentry(config_entry_1, "mock-subentry-id-1-1")
    entry = device_registry.async_get_device(identifiers={("bridgeid", "0123")})
    assert entry.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
    }

    hass.config_entries.async_remove_subentry(config_entry_1, "mock-subentry-id-1-2")
    entry = device_registry.async_get_device(identifiers={("bridgeid", "0123")})
    assert entry.config_entries == {config_entry_2.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_2.entry_id: {"mock-subentry-id-2-1"}
    }

    hass.config_entries.async_remove_subentry(config_entry_2, "mock-subentry-id-2-1")
    assert device_registry.async_get_device(identifiers={("bridgeid", "0123")}) is None
    assert device_registry.async_get_device(identifiers={("bridgeid", "4567")}) is None

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
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries_subentries": {
                config_entry_1.entry_id: {
                    None,
                    "mock-subentry-id-1-1",
                    "mock-subentry-id-1-2",
                },
                config_entry_2.entry_id: {
                    "mock-subentry-id-2-1",
                },
            },
        },
    }
    assert update_events[5].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries_subentries": {
                config_entry_1.entry_id: {
                    "mock-subentry-id-1-1",
                    "mock-subentry-id-1-2",
                },
                config_entry_2.entry_id: {
                    "mock-subentry-id-2-1",
                },
            },
        },
    }
    assert update_events[6].data == {
        "action": "update",
        "device_id": entry.id,
        "changes": {
            "config_entries": {config_entry_1.entry_id, config_entry_2.entry_id},
            "config_entries_subentries": {
                config_entry_1.entry_id: {
                    "mock-subentry-id-1-2",
                },
                config_entry_2.entry_id: {
                    "mock-subentry-id-2-1",
                },
            },
            "primary_config_entry": config_entry_1.entry_id,
        },
    }
    assert update_events[7].data == {
        "action": "remove",
        "device_id": entry.id,
        "device": entry.dict_repr,
    }