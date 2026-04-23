async def test_options_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_tts_from_service_account_info: AsyncMock,
) -> None:
    """Test options flow."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_api_tts_from_service_account_info.list_voices.call_count == 1

    assert mock_config_entry.options == {}

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {
        "language",
        "gender",
        "voice",
        "encoding",
        "speed",
        "pitch",
        "gain",
        "profiles",
        "text_type",
        "stt_model",
    }
    assert mock_api_tts_from_service_account_info.list_voices.call_count == 2

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"language": "el-GR"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {
        "language": "el-GR",
        "gender": "NEUTRAL",
        "voice": "",
        "encoding": "MP3",
        "speed": 1.0,
        "pitch": 0.0,
        "gain": 0.0,
        "profiles": [],
        "text_type": "text",
        "stt_model": "latest_short",
    }
    assert mock_api_tts_from_service_account_info.list_voices.call_count == 3