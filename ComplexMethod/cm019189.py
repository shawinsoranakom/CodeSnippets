async def test_subflow_reconfigure_already_configured(
    hass: HomeAssistant,
    mock_fishaudio_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfiguring a TTS subentry to match an existing one."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    # Try to reconfigure the first subentry to match the second one (which already exists)
    first_subentry = [
        s for s in mock_config_entry.subentries.values() if s.title == "Test Voice"
    ][0]

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "tts"),
        context={"source": "reconfigure", "subentry_id": first_subentry.subentry_id},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Step through reconfigure
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_TITLE: "",
            CONF_LANGUAGE: "en",
            CONF_SORT_BY: "task_count",
            CONF_SELF_ONLY: False,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "model"

    # Try to set the same voice_id and backend as the second subentry
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_VOICE_ID: "voice-beta",
            CONF_BACKEND: "s1",
            CONF_LATENCY: "normal",
            CONF_NAME: "Test Voice Updated",
        },
    )

    # Should abort because this combination already exists
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"