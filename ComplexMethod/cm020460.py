async def test_options_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test options flow."""
    await setup_integration(hass, mock_config_entry)

    old_volume_resolution = mock_config_entry.options[OPTION_VOLUME_RESOLUTION]

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            OPTION_MAX_VOLUME: 42,
            OPTION_INPUT_SOURCES: [],
            OPTION_LISTENING_MODES: ["STEREO"],
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {OPTION_INPUT_SOURCES: "empty_input_source_list"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            OPTION_MAX_VOLUME: 42,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: [],
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {OPTION_LISTENING_MODES: "empty_listening_mode_list"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            OPTION_MAX_VOLUME: 42,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["STEREO"],
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "names"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            OPTION_INPUT_SOURCES: {"TV": "television"},
            OPTION_LISTENING_MODES: {"STEREO": "Duophonia"},
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        OPTION_VOLUME_RESOLUTION: old_volume_resolution,
        OPTION_MAX_VOLUME: 42.0,
        OPTION_INPUT_SOURCES: {"12": "television"},
        OPTION_LISTENING_MODES: {"00": "Duophonia"},
    }