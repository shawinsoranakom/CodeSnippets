async def test_remove_stale_device(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    location: MagicMock,
    another_device: MagicMock,
    client: MagicMock,
) -> None:
    """Test that the stale device is removed."""
    location.devices_by_id[another_device.deviceid] = another_device

    config_entry_other = MockConfigEntry(
        domain="OtherDomain",
        data={},
        unique_id="unique_id",
    )
    config_entry_other.add_to_hass(hass)
    device_entry_other = device_registry.async_get_or_create(
        config_entry_id=config_entry_other.entry_id,
        identifiers={("OtherDomain", 7654321)},
    )

    config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        device_entry_other.id,
        add_config_entry_id=config_entry.entry_id,
        merge_identifiers={(DOMAIN, 7654321)},
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.async_entity_ids_count() == 8

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )

    device_entries_other = dr.async_entries_for_config_entry(
        device_registry, config_entry_other.entry_id
    )

    assert len(device_entries) == 2
    assert any((DOMAIN, 1234567) in device.identifiers for device in device_entries)
    assert any((DOMAIN, 7654321) in device.identifiers for device in device_entries)
    assert any(
        ("OtherDomain", 7654321) in device.identifiers for device in device_entries
    )
    assert len(device_entries_other) == 1
    assert any(
        ("OtherDomain", 7654321) in device.identifiers
        for device in device_entries_other
    )
    assert any(
        (DOMAIN, 7654321) in device.identifiers for device in device_entries_other
    )

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED

    del location.devices_by_id[another_device.deviceid]

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert (
        hass.states.async_entity_ids_count() == 4
    )  # 1 climate entities; 2 sensor entities; 1 switch entity

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    assert len(device_entries) == 1
    assert any((DOMAIN, 1234567) in device.identifiers for device in device_entries)
    assert not any((DOMAIN, 7654321) in device.identifiers for device in device_entries)
    assert not any(
        ("OtherDomain", 7654321) in device.identifiers for device in device_entries
    )

    device_entries_other = dr.async_entries_for_config_entry(
        device_registry, config_entry_other.entry_id
    )
    assert len(device_entries_other) == 1
    assert any(
        ("OtherDomain", 7654321) in device.identifiers
        for device in device_entries_other
    )