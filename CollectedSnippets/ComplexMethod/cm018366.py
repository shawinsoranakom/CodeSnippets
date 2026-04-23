async def test_creating_tts_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
) -> None:
    """Test creating a TTS subentry."""
    old_subentries = set(mock_config_entry.subentries)
    # Original conversation + ai_task + stt + tts
    assert len(mock_config_entry.subentries) == 4

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "tts"),
        context={"source": config_entries.SOURCE_USER},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "init"
    assert not result.get("errors")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": "Custom TTS",
            CONF_PROMPT: "Speak like a drunk pirate",
            CONF_TTS_SPEED: 0.85,
        },
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Custom TTS"
    assert result.get("data") == {
        CONF_PROMPT: "Speak like a drunk pirate",
        CONF_TTS_SPEED: 0.85,
        CONF_CHAT_MODEL: "gpt-4o-mini-tts",
    }

    assert (
        len(mock_config_entry.subentries) == 5
    )  # Original conversation + ai_task + stt + tts + new tts

    new_subentry_id = list(set(mock_config_entry.subentries) - old_subentries)[0]
    new_subentry = mock_config_entry.subentries[new_subentry_id]
    assert new_subentry.subentry_type == "tts"
    assert new_subentry.title == "Custom TTS"