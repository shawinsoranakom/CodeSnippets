async def test_options_flow_voice_settings_default(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_async_client: AsyncMock,
    mock_entry: MockConfigEntry,
) -> None:
    """Test options flow voice settings."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MODEL: "model1",
            CONF_VOICE: "voice1",
            CONF_STT_MODEL: "scribe_v1_experimental",
            CONF_STT_AUTO_LANGUAGE: False,
            CONF_CONFIGURE_VOICE: True,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "voice_settings"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_entry.options == {
        CONF_MODEL: "model1",
        CONF_VOICE: "voice1",
        CONF_STT_MODEL: "scribe_v1_experimental",
        CONF_STT_AUTO_LANGUAGE: False,
        CONF_SIMILARITY: DEFAULT_SIMILARITY,
        CONF_STABILITY: DEFAULT_STABILITY,
        CONF_STYLE: DEFAULT_STYLE,
        CONF_USE_SPEAKER_BOOST: DEFAULT_USE_SPEAKER_BOOST,
    }