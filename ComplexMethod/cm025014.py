async def test_update_remove_config_subentries(
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
    config_entry_3 = MockConfigEntry()
    config_entry_3.add_to_hass(hass)

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1-1",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry_id = entry.id
    assert entry.config_entries == {config_entry_1.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-1"}
    }

    entry = device_registry.async_update_device(
        entry_id,
        add_config_entry_id=config_entry_1.entry_id,
        add_config_subentry_id="mock-subentry-id-1-2",
    )
    assert entry.config_entries == {config_entry_1.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-1", "mock-subentry-id-1-2"}
    }

    # Try adding the same subentry again
    assert (
        device_registry.async_update_device(
            entry_id,
            add_config_entry_id=config_entry_1.entry_id,
            add_config_subentry_id="mock-subentry-id-1-2",
        )
        is entry
    )

    entry = device_registry.async_update_device(
        entry_id,
        add_config_entry_id=config_entry_2.entry_id,
        add_config_subentry_id="mock-subentry-id-2-1",
    )
    assert entry.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-1", "mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
    }

    entry = device_registry.async_update_device(
        entry_id,
        add_config_entry_id=config_entry_3.entry_id,
        add_config_subentry_id=None,
    )
    assert entry.config_entries == {
        config_entry_1.entry_id,
        config_entry_2.entry_id,
        config_entry_3.entry_id,
    }
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-1", "mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
        config_entry_3.entry_id: {None},
    }

    # Try to add a subentry without specifying entry
    with pytest.raises(
        HomeAssistantError,
        match="Can't add config subentry without specifying config entry",
    ):
        device_registry.async_update_device(entry_id, add_config_subentry_id="blabla")

    # Try to add an unknown subentry
    with pytest.raises(
        HomeAssistantError,
        match=f"Config entry {config_entry_3.entry_id} has no subentry blabla",
    ):
        device_registry.async_update_device(
            entry_id,
            add_config_entry_id=config_entry_3.entry_id,
            add_config_subentry_id="blabla",
        )

    # Try to remove a subentry without specifying entry
    with pytest.raises(
        HomeAssistantError,
        match="Can't remove config subentry without specifying config entry",
    ):
        device_registry.async_update_device(
            entry_id, remove_config_subentry_id="blabla"
        )

    assert len(device_registry.devices) == 1

    entry = device_registry.async_update_device(
        entry_id,
        remove_config_entry_id=config_entry_1.entry_id,
        remove_config_subentry_id="mock-subentry-id-1-1",
    )
    assert entry.config_entries == {
        config_entry_1.entry_id,
        config_entry_2.entry_id,
        config_entry_3.entry_id,
    }
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {"mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
        config_entry_3.entry_id: {None},
    }

    # Try removing the same subentry again
    assert (
        device_registry.async_update_device(
            entry_id,
            remove_config_entry_id=config_entry_1.entry_id,
            remove_config_subentry_id="mock-subentry-id-1-1",
        )
        is entry
    )

    entry = device_registry.async_update_device(
        entry_id,
        remove_config_entry_id=config_entry_1.entry_id,
        remove_config_subentry_id="mock-subentry-id-1-2",
    )
    assert entry.config_entries == {config_entry_2.entry_id, config_entry_3.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
        config_entry_3.entry_id: {None},
    }

    entry = device_registry.async_update_device(
        entry_id,
        remove_config_entry_id=config_entry_2.entry_id,
        remove_config_subentry_id="mock-subentry-id-2-1",
    )
    assert entry.config_entries == {config_entry_3.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_3.entry_id: {None},
    }

    entry_before_remove = entry
    entry = device_registry.async_update_device(
        entry_id,
        remove_config_entry_id=config_entry_3.entry_id,
        remove_config_subentry_id=None,
    )
    assert entry is None

    await hass.async_block_till_done()

    assert len(update_events) == 8
    assert update_events[0].data == {
        "action": "create",
        "device_id": entry_id,
    }
    assert update_events[1].data == {
        "action": "update",
        "device_id": entry_id,
        "changes": {
            "config_entries_subentries": {
                config_entry_1.entry_id: {"mock-subentry-id-1-1"}
            },
        },
    }
    assert update_events[2].data == {
        "action": "update",
        "device_id": entry_id,
        "changes": {
            "config_entries": {config_entry_1.entry_id},
            "config_entries_subentries": {
                config_entry_1.entry_id: {
                    "mock-subentry-id-1-1",
                    "mock-subentry-id-1-2",
                }
            },
        },
    }
    assert update_events[3].data == {
        "action": "update",
        "device_id": entry_id,
        "changes": {
            "config_entries": {config_entry_1.entry_id, config_entry_2.entry_id},
            "config_entries_subentries": {
                config_entry_1.entry_id: {
                    "mock-subentry-id-1-1",
                    "mock-subentry-id-1-2",
                },
                config_entry_2.entry_id: {"mock-subentry-id-2-1"},
            },
        },
    }
    assert update_events[4].data == {
        "action": "update",
        "device_id": entry_id,
        "changes": {
            "config_entries_subentries": {
                config_entry_1.entry_id: {
                    "mock-subentry-id-1-1",
                    "mock-subentry-id-1-2",
                },
                config_entry_2.entry_id: {"mock-subentry-id-2-1"},
                config_entry_3.entry_id: {None},
            },
        },
    }
    assert update_events[5].data == {
        "action": "update",
        "device_id": entry_id,
        "changes": {
            "config_entries": {
                config_entry_1.entry_id,
                config_entry_2.entry_id,
                config_entry_3.entry_id,
            },
            "config_entries_subentries": {
                config_entry_1.entry_id: {
                    "mock-subentry-id-1-2",
                },
                config_entry_2.entry_id: {"mock-subentry-id-2-1"},
                config_entry_3.entry_id: {None},
            },
            "primary_config_entry": config_entry_1.entry_id,
        },
    }
    assert update_events[6].data == {
        "action": "update",
        "device_id": entry_id,
        "changes": {
            "config_entries": {config_entry_2.entry_id, config_entry_3.entry_id},
            "config_entries_subentries": {
                config_entry_2.entry_id: {"mock-subentry-id-2-1"},
                config_entry_3.entry_id: {None},
            },
        },
    }
    assert update_events[7].data == {
        "action": "remove",
        "device_id": entry_id,
        "device": entry_before_remove.dict_repr,
    }