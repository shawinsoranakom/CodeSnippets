async def test_removing_labels(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Make sure we can clear labels."""
    config_entry = MockConfigEntry()
    config_entry.add_to_hass(hass)
    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    entry = device_registry.async_update_device(entry.id, labels={"label1", "label2"})

    device_registry.async_clear_label_id("label1")
    entry_cleared_label1 = device_registry.async_get_device({("bridgeid", "0123")})

    device_registry.async_clear_label_id("label2")
    entry_cleared_label2 = device_registry.async_get_device({("bridgeid", "0123")})

    assert entry_cleared_label1
    assert entry_cleared_label2
    assert entry != entry_cleared_label1
    assert entry != entry_cleared_label2
    assert entry_cleared_label1 != entry_cleared_label2
    assert entry.labels == {"label1", "label2"}
    assert entry_cleared_label1.labels == {"label2"}
    assert not entry_cleared_label2.labels