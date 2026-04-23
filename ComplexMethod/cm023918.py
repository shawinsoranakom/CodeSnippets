async def test_options_flow_bluetooth_required_for_offline_mode(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test options flow validates that Bluetooth is required when offline mode is enabled."""
    await async_init_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_USE_BLUETOOTH: False,
            CONF_OFFLINE_MODE: True,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {CONF_USE_BLUETOOTH: "bluetooth_required_offline"}

    # recover
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_USE_BLUETOOTH: True,
            CONF_OFFLINE_MODE: True,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_USE_BLUETOOTH: True,
        CONF_OFFLINE_MODE: True,
    }