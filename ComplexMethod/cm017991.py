async def test_remove_subentry(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we can remove a subentry."""
    subentry_id = "blabla"
    update_listener_calls = []

    async def mock_setup_entry(
        hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> bool:
        """Mock setting up entry."""
        await hass.config_entries.async_forward_entry_setups(entry, ["light"])
        return True

    mock_remove_entry = AsyncMock(return_value=None)

    entry_entity = MockEntity(unique_id="0001", name="Test Entry Entity")
    subentry_entity = MockEntity(unique_id="0002", name="Test Subentry Entity")

    async def mock_setup_entry_platform(
        hass: HomeAssistant,
        entry: config_entries.ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Mock setting up platform."""
        async_add_entities([entry_entity])
        async_add_entities([subentry_entity], config_subentry_id=subentry_id)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=mock_setup_entry,
            async_remove_entry=mock_remove_entry,
        ),
    )
    mock_platform(
        hass, "test.light", MockPlatform(async_setup_entry=mock_setup_entry_platform)
    )
    mock_platform(hass, "test.config_flow", None)

    entry = MockConfigEntry(
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={"first": True},
                subentry_id=subentry_id,
                subentry_type="test",
                unique_id="unique",
                title="Mock title",
            )
        ]
    )

    async def update_listener(
        hass: HomeAssistant, entry: config_entries.ConfigEntry
    ) -> None:
        """Test function."""
        assert entry.subentries == {}
        update_listener_calls.append(None)

    entry.add_update_listener(update_listener)
    entry.add_to_manager(manager)

    # Setup entry
    await manager.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Check entity states got added
    assert hass.states.get("light.test_entry_entity") is not None
    assert hass.states.get("light.test_subentry_entity") is not None
    assert len(hass.states.async_all()) == 2

    # Check entities got added to entity registry
    assert len(entity_registry.entities) == 2
    entry_entity_entry = entity_registry.entities["light.test_entry_entity"]
    assert entry_entity_entry.config_entry_id == entry.entry_id
    assert entry_entity_entry.config_subentry_id is None
    subentry_entity_entry = entity_registry.entities["light.test_subentry_entity"]
    assert subentry_entity_entry.config_entry_id == entry.entry_id
    assert subentry_entity_entry.config_subentry_id == subentry_id

    # Remove subentry
    result = manager.async_remove_subentry(entry, subentry_id)
    assert len(update_listener_calls) == 1
    await hass.async_block_till_done()

    # Check that remove went well
    assert result is True

    # Check the remove callback was not invoked.
    assert mock_remove_entry.call_count == 0

    # Check that the config subentry was removed.
    assert entry.subentries == {}

    # Check that entity state has been removed
    assert hass.states.get("light.test_entry_entity") is not None
    assert hass.states.get("light.test_subentry_entity") is None
    assert len(hass.states.async_all()) == 1

    # Check that entity registry entry has been removed
    entity_entry_list = list(entity_registry.entities)
    assert entity_entry_list == ["light.test_entry_entity"]

    # Try to remove the subentry again
    with pytest.raises(config_entries.UnknownSubEntry):
        manager.async_remove_subentry(entry, subentry_id)
    assert len(update_listener_calls) == 1