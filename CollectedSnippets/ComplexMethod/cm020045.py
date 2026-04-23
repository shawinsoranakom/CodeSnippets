async def test_options_flow(hass: HomeAssistant, mock_setup: Mock) -> None:
    """Test config flow options."""

    # Setup config flow
    result = await complete_flow(hass)
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == HOST
    assert "result" in result
    assert result["result"].data == CONFIG_ENTRY_DATA
    assert result["result"].options == {ATTR_DURATION: 6}

    # Assert single config entry is loaded
    config_entry = next(iter(hass.config_entries.async_entries(DOMAIN)))
    assert config_entry.state is ConfigEntryState.LOADED

    # Initiate the options flow
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "init"

    # Change the default duration
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={ATTR_DURATION: 5}
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        ATTR_DURATION: 5,
    }