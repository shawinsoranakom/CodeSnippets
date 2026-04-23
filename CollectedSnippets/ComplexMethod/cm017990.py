async def test_remove_entry(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we can remove an entry."""

    async def mock_setup_entry(
        hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> bool:
        """Mock setting up entry."""
        await hass.config_entries.async_forward_entry_setups(entry, ["light"])
        return True

    async def mock_unload_entry(
        hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> bool:
        """Mock unloading an entry."""
        result = await hass.config_entries.async_unload_platforms(entry, ["light"])
        assert result
        return result

    remove_entry_calls = []

    async def mock_remove_entry(
        hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> None:
        """Mock removing an entry."""
        # Check that the entry is no longer in the config entries
        assert not hass.config_entries.async_get_entry(entry.entry_id)
        remove_entry_calls.append(None)

    entity = MockEntity(unique_id="1234", name="Test Entity")

    async def mock_setup_entry_platform(
        hass: HomeAssistant,
        entry: config_entries.ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Mock setting up platform."""
        async_add_entities([entity])

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=mock_setup_entry,
            async_unload_entry=mock_unload_entry,
            async_remove_entry=mock_remove_entry,
        ),
    )
    mock_platform(
        hass, "test.light", MockPlatform(async_setup_entry=mock_setup_entry_platform)
    )
    mock_platform(hass, "test.config_flow", None)

    MockConfigEntry(domain="test_other", entry_id="test1").add_to_manager(manager)
    entry = MockConfigEntry(domain="test", entry_id="test2")
    entry.add_to_manager(manager)
    MockConfigEntry(domain="test_other", entry_id="test3").add_to_manager(manager)

    # Check all config entries exist
    assert manager.async_entry_ids() == [
        "test1",
        "test2",
        "test3",
    ]

    # Setup entry
    await manager.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Check entity state got added
    assert hass.states.get("light.test_entity") is not None
    assert len(hass.states.async_all()) == 1

    # Check entity got added to entity registry
    assert len(entity_registry.entities) == 1
    entity_entry = list(entity_registry.entities.values())[0]
    assert entity_entry.config_entry_id == entry.entry_id
    assert entity_entry.config_subentry_id is None

    # Remove entry
    result = await manager.async_remove("test2")
    await hass.async_block_till_done()

    # Check that unload went well and so no need to restart
    assert result == {"require_restart": False}

    # Check the remove callback was invoked.
    assert len(remove_entry_calls) == 1

    # Check that config entry was removed.
    assert manager.async_entry_ids() == ["test1", "test3"]

    # Check that entity state has been removed
    assert hass.states.get("light.test_entity") is None
    assert len(hass.states.async_all()) == 0

    # Check that entity registry entry has been removed
    entity_entry_list = list(entity_registry.entities.values())
    assert not entity_entry_list