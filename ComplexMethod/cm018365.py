async def test_creating_stt_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
) -> None:
    """Test creating a STT subentry."""
    old_subentries = set(mock_config_entry.subentries)
    # Original conversation + ai_task + stt + tts
    assert len(mock_config_entry.subentries) == 4

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "stt"),
        context={"source": config_entries.SOURCE_USER},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "init"
    assert not result.get("errors")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": "Custom STT",
            CONF_PROMPT: "Umm, let me think like, hmm… Okay, here’s what I’m, like, thinking.",
            CONF_CHAT_MODEL: "gpt-4o-transcribe",
        },
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Custom STT"
    assert result.get("data") == {
        CONF_PROMPT: "Umm, let me think like, hmm… Okay, here’s what I’m, like, thinking.",
        CONF_CHAT_MODEL: "gpt-4o-transcribe",
    }

    assert (
        len(mock_config_entry.subentries) == 5
    )  # Original conversation + ai_task + tts + original stt + new stt

    new_subentry_id = list(set(mock_config_entry.subentries) - old_subentries)[0]
    new_subentry = mock_config_entry.subentries[new_subentry_id]
    assert new_subentry.subentry_type == "stt"
    assert new_subentry.title == "Custom STT"