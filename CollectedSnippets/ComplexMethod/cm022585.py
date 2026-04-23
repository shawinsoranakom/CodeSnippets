async def test_config_entry_unique_id_update(
    hass: HomeAssistant,
    mock_lunatone_devices: AsyncMock,
    mock_lunatone_info: AsyncMock,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the Lunatone config entry migration to be successful."""
    config_entry = MockConfigEntry(
        title=BASE_URL,
        domain=DOMAIN,
        data={CONF_URL: BASE_URL},
        unique_id=str(SERIAL_NUMBER),
    )

    expected_unique_id = str(SERIAL_NUMBER)
    mock_lunatone_info.uid = None

    await setup_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.unique_id == expected_unique_id

    devices = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)
    for device in devices:
        for identifier in device.identifiers:
            assert identifier[1].startswith(expected_unique_id)

    entities = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    for entity in entities:
        assert entity.unique_id.startswith(expected_unique_id)

    expected_unique_id = UUID.replace("-", "")
    mock_lunatone_info.uid = UUID

    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.unique_id == expected_unique_id

    devices = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)
    for device in devices:
        for identifier in device.identifiers:
            assert identifier[1].startswith(expected_unique_id)

    entities = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    for entity in entities:
        assert entity.unique_id.startswith(expected_unique_id)