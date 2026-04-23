async def test_options_add_keypad_with_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_homeworks: MagicMock
) -> None:
    """Test options flow to add and remove a keypad."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "add_keypad"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_keypad"

    # Try an invalid address
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDR: "[02:08:03:01",
            CONF_NAME: "Hall Keypad",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_keypad"
    assert result["errors"] == {"base": "invalid_addr"}

    # Try an address claimed by another keypad
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDR: "[02:08:02:01]",
            CONF_NAME: "Hall Keypad",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_keypad"
    assert result["errors"] == {"base": "duplicated_addr"}

    # Try an address claimed by a light
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDR: "[02:08:01:01]",
            CONF_NAME: "Hall Keypad",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_keypad"
    assert result["errors"] == {"base": "duplicated_addr"}