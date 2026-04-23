async def test_async_loaded_entries(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test that we can get loaded config entries."""
    entry1 = MockConfigEntry(domain="comp")
    entry1.add_to_hass(hass)
    entry2 = MockConfigEntry(domain="comp", source=config_entries.SOURCE_IGNORE)
    entry2.add_to_hass(hass)
    entry3 = MockConfigEntry(
        domain="comp", disabled_by=config_entries.ConfigEntryDisabler.USER
    )
    entry3.add_to_hass(hass)

    mock_setup = AsyncMock(return_value=True)
    mock_setup_entry = AsyncMock(return_value=True)
    mock_unload_entry = AsyncMock(return_value=True)

    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup=mock_setup,
            async_setup_entry=mock_setup_entry,
            async_unload_entry=mock_unload_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)

    assert hass.config_entries.async_loaded_entries("comp") == []

    assert await manager.async_setup(entry1.entry_id)
    assert not await manager.async_setup(entry2.entry_id)
    assert not await manager.async_setup(entry3.entry_id)

    assert hass.config_entries.async_loaded_entries("comp") == [entry1]

    assert await hass.config_entries.async_unload(entry1.entry_id)

    assert hass.config_entries.async_loaded_entries("comp") == []