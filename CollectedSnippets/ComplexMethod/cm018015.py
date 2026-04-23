async def test_entry_reload_calls_on_unload_listeners(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test reload calls the on unload listeners."""
    entry = MockConfigEntry(domain="comp", state=config_entries.ConfigEntryState.LOADED)
    entry.add_to_hass(hass)

    async_setup = AsyncMock(return_value=True)
    mock_setup_entry = AsyncMock(return_value=True)
    async_unload_entry = AsyncMock(return_value=True)

    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup=async_setup,
            async_setup_entry=mock_setup_entry,
            async_unload_entry=async_unload_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)
    hass.config.components.add("comp")

    mock_unload_callback = Mock()

    entry.async_on_unload(mock_unload_callback)

    assert await manager.async_reload(entry.entry_id)
    assert len(async_unload_entry.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_unload_callback.mock_calls) == 1
    assert entry.state is config_entries.ConfigEntryState.LOADED

    assert await manager.async_reload(entry.entry_id)
    assert len(async_unload_entry.mock_calls) == 2
    assert len(mock_setup_entry.mock_calls) == 2
    # Since we did not register another async_on_unload it should
    # have only been called once
    assert len(mock_unload_callback.mock_calls) == 1
    assert entry.state is config_entries.ConfigEntryState.LOADED