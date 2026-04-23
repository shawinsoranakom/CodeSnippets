async def test_context_no_leak(hass: HomeAssistant) -> None:
    """Test ensure that config entry context does not leak.

    Unlikely to happen in real world, but occurs often in tests.
    """

    connected_future = asyncio.Future()
    bg_tasks = []

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock setup entry."""

        async def _async_set_runtime_data():
            # Show that config_entries.current_entry is preserved for child tasks
            await connected_future
            entry.runtime_data = config_entries.current_entry.get()

        bg_tasks.append(hass.loop.create_task(_async_set_runtime_data()))

        return True

    async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock unload entry."""
        return True

    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup_entry=async_setup_entry,
            async_unload_entry=async_unload_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)

    entry1 = MockConfigEntry(domain="comp")
    entry1.add_to_hass(hass)

    await hass.config_entries.async_setup(entry1.entry_id)
    assert entry1.state is config_entries.ConfigEntryState.LOADED
    assert config_entries.current_entry.get() is None

    # Load an existing config entry
    entry2 = MockConfigEntry(domain="comp")
    entry2.add_to_hass(hass)
    await hass.config_entries.async_setup(entry2.entry_id)
    assert entry2.state is config_entries.ConfigEntryState.LOADED
    assert config_entries.current_entry.get() is None

    # Add a new config entry (eg. from config flow)
    entry3 = MockConfigEntry(domain="comp")
    await hass.config_entries.async_add(entry3)
    assert entry3.state is config_entries.ConfigEntryState.LOADED
    assert config_entries.current_entry.get() is None

    for entry in (entry1, entry2, entry3):
        assert entry.state is config_entries.ConfigEntryState.LOADED
        assert not hasattr(entry, "runtime_data")
    assert config_entries.current_entry.get() is None

    connected_future.set_result(None)
    await asyncio.gather(*bg_tasks)

    for entry in (entry1, entry2, entry3):
        assert entry.state is config_entries.ConfigEntryState.LOADED
        assert entry.runtime_data is entry
    assert config_entries.current_entry.get() is None