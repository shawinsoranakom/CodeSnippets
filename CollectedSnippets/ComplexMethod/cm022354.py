async def test_options_add_button_flow_duplicate(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_homeworks: MagicMock
) -> None:
    """Test options flow to add a button."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids(BINARY_SENSOR_DOMAIN)) == 2
    assert len(hass.states.async_entity_ids(BUTTON_DOMAIN)) == 3

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "select_edit_keypad"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_edit_keypad"
    assert result["data_schema"].schema["index"].container == {
        "0": "Foyer Keypad ([02:08:02:01])"
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"index": "0"},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "edit_keypad"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_button"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_button"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Dim down",
            CONF_NUMBER: 1,
            CONF_RELEASE_DELAY: 0.2,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "duplicated_number"}