async def test_options_flow_triggers_reauth(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Test load and unload of a ConfigEntry."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.google.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.async_setup(config_entry.entry_id)
        mock_setup.assert_called_once()

    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.options == {}  # Default is read_write

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {"calendar_access"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "calendar_access": "read_only",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"calendar_access": "read_only"}