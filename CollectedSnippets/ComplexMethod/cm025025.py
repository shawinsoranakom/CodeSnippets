async def test_removing_labels_deleted_device(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Make sure we can clear labels."""
    config_entry = MockConfigEntry()
    config_entry.add_to_hass(hass)
    entry1 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry1 = device_registry.async_update_device(entry1.id, labels={"label1", "label2"})
    entry2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
        identifiers={("bridgeid", "1234")},
        manufacturer="manufacturer",
        model="model",
    )
    entry2 = device_registry.async_update_device(entry2.id, labels={"label3"})

    device_registry.async_remove_device(entry1.id)
    device_registry.async_remove_device(entry2.id)

    device_registry.async_clear_label_id("label1")
    entry1_cleared_label1 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
    )

    device_registry.async_remove_device(entry1.id)

    device_registry.async_clear_label_id("label2")
    entry1_cleared_label2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
    )
    entry2_restored = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
        identifiers={("bridgeid", "1234")},
    )

    assert entry1_cleared_label1
    assert entry1_cleared_label2
    assert entry1 != entry1_cleared_label1
    assert entry1 != entry1_cleared_label2
    assert entry1_cleared_label1 != entry1_cleared_label2
    assert entry1.labels == {"label1", "label2"}
    assert entry1_cleared_label1.labels == {"label2"}
    assert not entry1_cleared_label2.labels
    assert entry2 != entry2_restored
    assert entry2_restored.labels == {"label3"}