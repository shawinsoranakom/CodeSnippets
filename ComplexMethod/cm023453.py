async def test_migrate_entry_from_v2_2(hass: HomeAssistant) -> None:
    """Test migration from version 2.2."""
    # Create a v2.2 config entry with conversation and TTS subentries
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test-api-key"},
        version=2,
        minor_version=2,
        subentries_data=[
            {
                "data": RECOMMENDED_CONVERSATION_OPTIONS,
                "subentry_type": "conversation",
                "title": DEFAULT_CONVERSATION_NAME,
                "unique_id": None,
            },
            {
                "data": RECOMMENDED_TTS_OPTIONS,
                "subentry_type": "tts",
                "title": DEFAULT_TTS_NAME,
                "unique_id": None,
            },
        ],
    )
    mock_config_entry.add_to_hass(hass)

    # Verify initial state
    assert mock_config_entry.version == 2
    assert mock_config_entry.minor_version == 2
    assert len(mock_config_entry.subentries) == 2

    # Run setup to trigger migration
    with patch(
        "homeassistant.components.google_generative_ai_conversation.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        assert result is True
        await hass.async_block_till_done()

    # Verify migration completed
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]

    # Check version and subversion were updated
    assert entry.version == 2
    assert entry.minor_version == 4

    # Check we now have conversation, tts, stt, and ai_task_data subentries
    assert len(entry.subentries) == 4

    subentries = {
        subentry.subentry_type: subentry for subentry in entry.subentries.values()
    }
    assert "conversation" in subentries
    assert "tts" in subentries
    assert "ai_task_data" in subentries

    # Find and verify the ai_task_data subentry
    ai_task_subentry = subentries["ai_task_data"]
    assert ai_task_subentry is not None
    assert ai_task_subentry.title == DEFAULT_AI_TASK_NAME
    assert ai_task_subentry.data == RECOMMENDED_AI_TASK_OPTIONS

    # Find and verify the stt subentry
    ai_task_subentry = subentries["stt"]
    assert ai_task_subentry is not None
    assert ai_task_subentry.title == DEFAULT_STT_NAME
    assert ai_task_subentry.data == RECOMMENDED_STT_OPTIONS

    # Verify conversation subentry is still there and unchanged
    conversation_subentry = subentries["conversation"]
    assert conversation_subentry is not None
    assert conversation_subentry.title == DEFAULT_CONVERSATION_NAME
    assert conversation_subentry.data == RECOMMENDED_CONVERSATION_OPTIONS

    # Verify TTS subentry is still there and unchanged
    tts_subentry = subentries["tts"]
    assert tts_subentry is not None
    assert tts_subentry.title == DEFAULT_TTS_NAME
    assert tts_subentry.data == RECOMMENDED_TTS_OPTIONS