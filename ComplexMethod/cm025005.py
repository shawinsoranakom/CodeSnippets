async def test_multiple_config_subentries(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Make sure we do not get duplicate entries."""
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
    assert entry.config_entries == {config_entry_1.entry_id}
    assert entry.config_entries_subentries == {config_entry_1.entry_id: {None}}
    entry_id = entry.id

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id=None,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    assert entry.id == entry_id
    assert entry.config_entries == {config_entry_1.entry_id}
    assert entry.config_entries_subentries == {config_entry_1.entry_id: {None}}

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1-1",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    assert entry.id == entry_id
    assert entry.config_entries == {config_entry_1.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {None, "mock-subentry-id-1-1"}
    }

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1-2",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    assert entry.id == entry_id
    assert entry.config_entries == {config_entry_1.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {None, "mock-subentry-id-1-1", "mock-subentry-id-1-2"}
    }

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        config_subentry_id="mock-subentry-id-2-1",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    assert entry.id == entry_id
    assert entry.config_entries == {config_entry_1.entry_id, config_entry_2.entry_id}
    assert entry.config_entries_subentries == {
        config_entry_1.entry_id: {None, "mock-subentry-id-1-1", "mock-subentry-id-1-2"},
        config_entry_2.entry_id: {"mock-subentry-id-2-1"},
    }