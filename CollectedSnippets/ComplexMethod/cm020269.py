async def test_migrate_entry_from_v1_1_to_v1_2(
    hass: HomeAssistant,
) -> None:
    """Test migration from version 1.1 to 1.2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "bla",
        },
        version=1,
        minor_version=1,
        subentries_data=[
            ConfigSubentryData(
                data={
                    CONF_MODEL: "openai/gpt-3.5-turbo",
                    CONF_PROMPT: "You are a helpful assistant.",
                    CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
                },
                subentry_id="conversation_subentry",
                subentry_type="conversation",
                title="GPT-3.5 Turbo",
                unique_id=None,
            ),
            ConfigSubentryData(
                data={
                    CONF_MODEL: "openai/gpt-4",
                },
                subentry_id="ai_task_subentry",
                subentry_type="ai_task_data",
                title="GPT-4",
                unique_id=None,
            ),
        ],
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.open_router.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.version == 1
    assert entry.minor_version == 2

    conversation_subentry = entry.subentries["conversation_subentry"]
    assert conversation_subentry.data[CONF_MODEL] == "openai/gpt-3.5-turbo"
    assert conversation_subentry.data[CONF_PROMPT] == "You are a helpful assistant."
    assert conversation_subentry.data[CONF_LLM_HASS_API] == [llm.LLM_API_ASSIST]
    assert conversation_subentry.data[CONF_WEB_SEARCH] is False

    ai_task_subentry = entry.subentries["ai_task_subentry"]
    assert ai_task_subentry.data[CONF_MODEL] == "openai/gpt-4"
    assert ai_task_subentry.data[CONF_WEB_SEARCH] is False