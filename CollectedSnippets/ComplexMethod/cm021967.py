async def test_migration_from_v1_to_v2_with_same_keys(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from version 1 to version 2 with same API keys consolidates entries."""
    # Create two v1 config entries with the same API key
    options = {
        "recommended": True,
        "llm_hass_api": ["assist"],
        "prompt": "You are a helpful assistant",
        "chat_model": "claude-haiku-4-5",
    }
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"api_key": "1234"},
        options=options,
        version=1,
        title="Claude",
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry_2 = MockConfigEntry(
        domain=DOMAIN,
        data={"api_key": "1234"},  # Same API key
        options=options,
        version=1,
        title="Claude 2",
    )
    mock_config_entry_2.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, mock_config_entry.entry_id)},
        name=mock_config_entry.title,
        manufacturer="Anthropic",
        model="Claude",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry.entry_id,
        config_entry=mock_config_entry,
        device_id=device.id,
        suggested_object_id="claude",
    )

    device_2 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_2.entry_id,
        identifiers={(DOMAIN, mock_config_entry_2.entry_id)},
        name=mock_config_entry_2.title,
        manufacturer="Anthropic",
        model="Claude",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry_2.entry_id,
        config_entry=mock_config_entry_2,
        device_id=device_2.id,
        suggested_object_id="claude_2",
    )

    # Run migration
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Should have only one entry left (consolidated)
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    entry = entries[0]
    assert entry.version == 2
    assert entry.minor_version == MINOR_VERSION
    assert not entry.options
    assert len(entry.subentries) == 2  # Two subentries from the two original entries

    # Check both subentries exist with correct data
    subentries = list(entry.subentries.values())
    titles = [sub.title for sub in subentries]
    assert "Claude" in titles
    assert "Claude 2" in titles

    for subentry in subentries:
        assert subentry.subentry_type == "conversation"
        assert subentry.data == options

        # Check devices were migrated correctly
        dev = device_registry.async_get_device(
            identifiers={(DOMAIN, subentry.subentry_id)}
        )
        assert dev is not None
        assert dev.config_entries == {mock_config_entry.entry_id}
        assert dev.config_entries_subentries == {
            mock_config_entry.entry_id: {subentry.subentry_id}
        }