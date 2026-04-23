async def test_migration_from_v1(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from version 1 to version 2."""
    # Create a v1 config entry with conversation options and an entity
    OPTIONS = {
        "recommended": True,
        "llm_hass_api": ["assist"],
        "prompt": "You are a helpful assistant",
        "chat_model": "gpt-4o-mini",
    }
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"api_key": "1234"},
        options=OPTIONS,
        version=1,
        title="ChatGPT",
    )
    mock_config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, mock_config_entry.entry_id)},
        name=mock_config_entry.title,
        manufacturer="OpenAI",
        model="ChatGPT",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity = entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry.entry_id,
        config_entry=mock_config_entry,
        device_id=device.id,
        suggested_object_id="chatgpt",
    )

    # Run migration
    with patch(
        "homeassistant.components.openai_conversation.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.version == 2
    assert mock_config_entry.minor_version == 6
    assert mock_config_entry.data == {"api_key": "1234"}
    assert mock_config_entry.options == {}

    assert len(mock_config_entry.subentries) == 4

    # Find the subentries
    conversation_subentry = None
    ai_task_subentry = None
    stt_subentry = None
    tts_subentry = None
    for subentry in mock_config_entry.subentries.values():
        if subentry.subentry_type == "conversation":
            conversation_subentry = subentry
        elif subentry.subentry_type == "ai_task_data":
            ai_task_subentry = subentry
        elif subentry.subentry_type == "stt":
            stt_subentry = subentry
        elif subentry.subentry_type == "tts":
            tts_subentry = subentry
    assert conversation_subentry is not None
    assert conversation_subentry.unique_id is None
    assert conversation_subentry.title == "ChatGPT"
    assert conversation_subentry.subentry_type == "conversation"
    assert conversation_subentry.data == OPTIONS

    assert ai_task_subentry is not None
    assert ai_task_subentry.unique_id is None
    assert ai_task_subentry.title == DEFAULT_AI_TASK_NAME
    assert ai_task_subentry.subentry_type == "ai_task_data"

    assert stt_subentry is not None
    assert stt_subentry.unique_id is None
    assert stt_subentry.title == DEFAULT_STT_NAME
    assert stt_subentry.subentry_type == "stt"

    assert tts_subentry is not None
    assert tts_subentry.unique_id is None
    assert tts_subentry.title == DEFAULT_TTS_NAME
    assert tts_subentry.subentry_type == "tts"

    # Use conversation subentry for the rest of the assertions
    subentry = conversation_subentry

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