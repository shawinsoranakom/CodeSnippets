async def test_migrate_entry_from_v2_3(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    config_entry_disabled_by: ConfigEntryDisabler | None,
    device_disabled_by: DeviceEntryDisabler | None,
    entity_disabled_by: RegistryEntryDisabler | None,
    setup_result: bool,
    minor_version_after_migration: int,
    config_entry_disabled_by_after_migration: ConfigEntryDisabler | None,
    device_disabled_by_after_migration: ConfigEntryDisabler | None,
    entity_disabled_by_after_migration: RegistryEntryDisabler | None,
) -> None:
    """Test migration from version 2.3."""
    # Create a v2.3 config entry with conversation subentries
    conversation_subentry_id = "blabla"
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test-api-key"},
        disabled_by=config_entry_disabled_by,
        version=2,
        minor_version=3,
        subentries_data=[
            {
                "data": RECOMMENDED_CONVERSATION_OPTIONS,
                "subentry_id": conversation_subentry_id,
                "subentry_type": "conversation",
                "title": DEFAULT_CONVERSATION_NAME,
                "unique_id": None,
            },
        ],
    )
    mock_config_entry.add_to_hass(hass)

    conversation_device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        config_subentry_id=conversation_subentry_id,
        disabled_by=device_disabled_by,
        identifiers={(DOMAIN, mock_config_entry.entry_id)},
        name=mock_config_entry.title,
        manufacturer="OpenAI",
        model="ChatGPT",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    conversation_entity = entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry.entry_id,
        config_entry=mock_config_entry,
        config_subentry_id=conversation_subentry_id,
        disabled_by=entity_disabled_by,
        device_id=conversation_device.id,
        suggested_object_id="chatgpt",
    )

    # Verify initial state
    assert mock_config_entry.version == 2
    assert mock_config_entry.minor_version == 3
    assert len(mock_config_entry.subentries) == 1
    assert mock_config_entry.disabled_by == config_entry_disabled_by
    assert conversation_device.disabled_by == device_disabled_by
    assert conversation_entity.disabled_by == entity_disabled_by

    # Run setup to trigger migration
    with patch(
        "homeassistant.components.openai_conversation.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        assert result is setup_result
        await hass.async_block_till_done()

    # Verify migration completed
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]

    # Check version and subversion were updated
    assert entry.version == 2
    assert entry.minor_version == minor_version_after_migration

    # Check the disabled_by flag on config entry, device and entity are as expected
    conversation_device = device_registry.async_get(conversation_device.id)
    conversation_entity = entity_registry.async_get(conversation_entity.entity_id)
    assert mock_config_entry.disabled_by == config_entry_disabled_by_after_migration
    assert conversation_device.disabled_by == device_disabled_by_after_migration
    assert conversation_entity.disabled_by == entity_disabled_by_after_migration