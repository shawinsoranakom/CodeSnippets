async def test_entry_disable_succeed(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test that we can disable an entry."""
    entry = MockConfigEntry(domain="comp", state=config_entries.ConfigEntryState.LOADED)
    entry.add_to_hass(hass)

    async_setup = AsyncMock(return_value=True)
    async_setup_entry = AsyncMock(return_value=True)
    async_unload_entry = AsyncMock(return_value=True)

    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup=async_setup,
            async_setup_entry=async_setup_entry,
            async_unload_entry=async_unload_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)
    hass.config.components.add("comp")

    # Disable
    assert len(async_setup.mock_calls) == 0
    assert len(async_setup_entry.mock_calls) == 0
    assert await manager.async_set_disabled_by(
        entry.entry_id, config_entries.ConfigEntryDisabler.USER
    )
    assert len(async_unload_entry.mock_calls) == 1
    assert len(async_setup.mock_calls) == 0
    assert len(async_setup_entry.mock_calls) == 0
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED

    # Enable
    assert await manager.async_set_disabled_by(entry.entry_id, None)
    assert len(async_unload_entry.mock_calls) == 1
    assert len(async_setup.mock_calls) == 0
    assert len(async_setup_entry.mock_calls) == 1
    assert entry.state is config_entries.ConfigEntryState.LOADED