async def test_migration_from_v2_2(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from version 2.2."""
    # Create a v2.2 config entry with a conversation subentry
    options = {
        "recommended": True,
        "llm_hass_api": ["assist"],
        "prompt": "You are a helpful assistant",
        "chat_model": "gpt-4o-mini",
    }
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"api_key": "1234"},
        entry_id="mock_entry_id",
        version=2,
        minor_version=2,
        subentries_data=[
            ConfigSubentryData(
                data=options,
                subentry_id="mock_id_1",
                subentry_type="conversation",
                title="ChatGPT",
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
    assert conversation_subentry.data == options

    # Check AI Task subentry was added
    ai_task_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "ai_task_data"
    ]
    assert len(ai_task_subentries) == 1
    ai_task_subentry = ai_task_subentries[0]
    assert ai_task_subentry.data == {"recommended": True}
    assert ai_task_subentry.title == "OpenAI AI Task"