async def test_labels_removed_from_devices(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    label_registry: lr.LabelRegistry,
) -> None:
    """Test if label gets removed from devices when the label is removed."""
    config_entry = MockConfigEntry()
    config_entry.add_to_hass(hass)

    label1 = label_registry.async_create("label1")
    label2 = label_registry.async_create("label2")
    assert len(label_registry.labels) == 2

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:23")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    device_registry.async_update_device(entry.id, labels={label1.label_id})
    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:56")},
        identifiers={("bridgeid", "0456")},
        manufacturer="manufacturer",
        model="model",
    )
    device_registry.async_update_device(entry.id, labels={label2.label_id})
    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:89")},
        identifiers={("bridgeid", "0789")},
        manufacturer="manufacturer",
        model="model",
    )
    device_registry.async_update_device(
        entry.id, labels={label1.label_id, label2.label_id}
    )

    entries = dr.async_entries_for_label(device_registry, label1.label_id)
    assert len(entries) == 2
    entries = dr.async_entries_for_label(device_registry, label2.label_id)
    assert len(entries) == 2

    label_registry.async_delete(label1.label_id)
    await hass.async_block_till_done()

    entries = dr.async_entries_for_label(device_registry, label1.label_id)
    assert len(entries) == 0
    entries = dr.async_entries_for_label(device_registry, label2.label_id)
    assert len(entries) == 2

    label_registry.async_delete(label2.label_id)
    await hass.async_block_till_done()

    entries = dr.async_entries_for_label(device_registry, label1.label_id)
    assert len(entries) == 0
    entries = dr.async_entries_for_label(device_registry, label2.label_id)
    assert len(entries) == 0