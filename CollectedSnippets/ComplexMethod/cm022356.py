async def test_options_remove_button_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_homeworks: MagicMock
) -> None:
    """Test options flow to remove a button."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
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
        result["flow_id"], {"next_step_id": "remove_button"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "remove_button"
    assert result["data_schema"].schema["index"].options == {
        "0": "Morning (1)",
        "1": "Relax (2)",
        "2": "Dim up (3)",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_INDEX: ["0"]}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "controller_id": "main_controller",
        "dimmers": [{"addr": "[02:08:01:01]", "name": "Foyer Sconces", "rate": 1.0}],
        "host": "192.168.0.1",
        "keypads": [
            {
                "addr": "[02:08:02:01]",
                "buttons": [
                    {"led": True, "name": "Relax", "number": 2, "release_delay": None},
                    {"led": False, "name": "Dim up", "number": 3, "release_delay": 0.2},
                ],
                "name": "Foyer Keypad",
            }
        ],
        "port": 1234,
    }

    await hass.async_block_till_done()

    # Check the entities were removed
    assert len(hass.states.async_entity_ids(BINARY_SENSOR_DOMAIN)) == 1
    assert len(hass.states.async_entity_ids(BUTTON_DOMAIN)) == 2