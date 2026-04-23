async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    # Pretend we already set up a config entry.
    hass.config.components.add("google_generative_ai_conversation")
    MockConfigEntry(
        domain=DOMAIN,
        state=config_entries.ConfigEntryState.LOADED,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    with (
        patch(
            "google.genai.models.AsyncModels.list",
        ),
        patch(
            "homeassistant.components.google_generative_ai_conversation.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "bla",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        "api_key": "bla",
    }
    assert result2["options"] == {}
    assert result2["subentries"] == [
        {
            "subentry_type": "conversation",
            "data": RECOMMENDED_CONVERSATION_OPTIONS,
            "title": DEFAULT_CONVERSATION_NAME,
            "unique_id": None,
        },
        {
            "subentry_type": "tts",
            "data": RECOMMENDED_TTS_OPTIONS,
            "title": DEFAULT_TTS_NAME,
            "unique_id": None,
        },
        {
            "subentry_type": "ai_task_data",
            "data": RECOMMENDED_AI_TASK_OPTIONS,
            "title": DEFAULT_AI_TASK_NAME,
            "unique_id": None,
        },
        {
            "subentry_type": "stt",
            "data": RECOMMENDED_STT_OPTIONS,
            "title": DEFAULT_STT_NAME,
            "unique_id": None,
        },
    ]
    assert len(mock_setup_entry.mock_calls) == 1