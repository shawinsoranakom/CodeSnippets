async def test_subflow_happy_path(
    hass: HomeAssistant,
    mock_fishaudio_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the full subflow happy path."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "tts"),
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

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

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_VOICE_ID: "voice-alpha",
            CONF_BACKEND: "s1",
            CONF_LATENCY: "balanced",
            CONF_NAME: "My Custom Voice",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Custom Voice"
    assert result["data"][CONF_VOICE_ID] == "voice-alpha"
    assert result["data"][CONF_BACKEND] == "s1"
    assert result["data"][CONF_LATENCY] == "balanced"
    assert result["unique_id"] == "voice-alpha-s1"

    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert len(entry.subentries) == 3