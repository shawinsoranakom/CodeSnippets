async def test_migration_from_v2_5(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from version 2.5."""
    # Create a v2.5 config entry with a conversation, AI Task, and TTS subentries
    conversation_options = {
        "recommended": True,
        "llm_hass_api": ["assist"],
        "prompt": "You are a helpful assistant",
        "chat_model": "gpt-4o-mini",
    }
    ai_task_options = {
        "recommended": True,
        "chat_model": "gpt-5-mini",
    }
    tts_options = {
        "prompt": "Be friendly",
        "chat_model": "gpt-4o-mini-tts",
    }
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"api_key": "1234"},
        entry_id="mock_entry_id",
        version=2,
        minor_version=5,
        subentries_data=[
            ConfigSubentryData(
                data=conversation_options,
                subentry_id="mock_id_1",
                subentry_type="conversation",
                title="ChatGPT",
                unique_id=None,
            ),
            ConfigSubentryData(
                data=ai_task_options,
                subentry_id="mock_id_2",
                subentry_type="ai_task_data",
                title="OpenAI AI Task",
                unique_id=None,
            ),
            ConfigSubentryData(
                data=tts_options,
                subentry_id="mock_id_3",
                subentry_type="tts",
                title="OpenAI TTS",
                unique_id=None,
            ),
        ],
        title="ChatGPT",
    )
    mock_config_entry.add_to_hass(hass)

    # Run migration
    with patch(
        "homeassistant.components.openai_conversation.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.version == 2
    assert entry.minor_version == 6
    assert not entry.options
    assert entry.title == "ChatGPT"
    assert len(entry.subentries) == 4

    # Check conversation subentry is still there
    conversation_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "conversation"
    ]
    assert len(conversation_subentries) == 1
    conversation_subentry = conversation_subentries[0]
    assert conversation_subentry.data == conversation_options

    # Check AI Task subentry is still there
    ai_task_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "ai_task_data"
    ]
    assert len(ai_task_subentries) == 1
    ai_task_subentry = ai_task_subentries[0]
    assert ai_task_subentry.data == ai_task_options

    # Check TTS subentry is still there
    tts_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "tts"
    ]
    assert len(tts_subentries) == 1
    tts_subentry = tts_subentries[0]
    assert tts_subentry.data == tts_options

    # Check STT subentry was added
    stt_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "stt"
    ]
    assert len(stt_subentries) == 1
    stt_subentry = stt_subentries[0]
    assert stt_subentry.data == {}
    assert stt_subentry.title == "OpenAI STT"