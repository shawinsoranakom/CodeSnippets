async def test_migration_from_v1(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from version 1."""
    # Create a v1 config entry with conversation options and an entity
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=V1_TEST_USER_DATA,
        options=V1_TEST_OPTIONS,
        version=1,
        title="llama-3.2-8b",
    )
    mock_config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, mock_config_entry.entry_id)},
        name=mock_config_entry.title,
        manufacturer="Ollama",
        model="Ollama",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity = entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry.entry_id,
        config_entry=mock_config_entry,
        device_id=device.id,
        suggested_object_id="llama_3_2_8b",
    )

    # Run migration
    with patch(
        "homeassistant.components.ollama.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.version == 3
    assert mock_config_entry.minor_version == 3
    # After migration, parent entry should only have URL
    assert mock_config_entry.data == {CONF_URL: "http://localhost:11434"}
    assert mock_config_entry.options == {}

    assert len(mock_config_entry.subentries) == 2

    subentry = next(
        iter(
            entry
            for entry in mock_config_entry.subentries.values()
            if entry.subentry_type == "conversation"
        )
    )
    assert subentry.unique_id is None
    assert subentry.title == "llama-3.2-8b"
    assert subentry.subentry_type == "conversation"
    # Subentry should now include the model from the original options
    expected_subentry_data = TEST_OPTIONS.copy()
    assert subentry.data == expected_subentry_data

    # Find the AI Task subentry
    ai_task_subentry = next(
        iter(
            entry
            for entry in mock_config_entry.subentries.values()
            if entry.subentry_type == "ai_task_data"
        )
    )
    assert ai_task_subentry.unique_id is None
    assert ai_task_subentry.title == "Ollama AI Task"
    assert ai_task_subentry.subentry_type == "ai_task_data"

    migrated_entity = entity_registry.async_get(entity.entity_id)
    assert migrated_entity is not None
    assert migrated_entity.config_entry_id == mock_config_entry.entry_id
    assert migrated_entity.config_subentry_id == subentry.subentry_id
    assert migrated_entity.unique_id == subentry.subentry_id

    # Check device migration
    assert not device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry.entry_id)}
    )
    assert (
        migrated_device := device_registry.async_get_device(
            identifiers={(DOMAIN, subentry.subentry_id)}
        )
    )
    assert migrated_device.identifiers == {(DOMAIN, subentry.subentry_id)}
    assert migrated_device.id == device.id
    assert migrated_device.config_entries == {mock_config_entry.entry_id}
    assert migrated_device.config_entries_subentries == {
        mock_config_entry.entry_id: {subentry.subentry_id}
    }