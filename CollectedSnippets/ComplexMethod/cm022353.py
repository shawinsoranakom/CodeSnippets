async def test_options_add_button_flow(
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
            CONF_NUMBER: 4,
            CONF_RELEASE_DELAY: 0.2,
            CONF_LED: True,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "controller_id": "main_controller",
        "dimmers": [{"addr": "[02:08:01:01]", "name": "Foyer Sconces", "rate": 1.0}],
        "host": "192.168.0.1",
        "keypads": [
            {
                "addr": "[02:08:02:01]",
                "buttons": [
                    {
                        "led": True,
                        "name": "Morning",
                        "number": 1,
                        "release_delay": None,
                    },
                    {"led": True, "name": "Relax", "number": 2, "release_delay": None},
                    {"led": False, "name": "Dim up", "number": 3, "release_delay": 0.2},
                    {
                        "led": True,
                        "name": "Dim down",
                        "number": 4,
                        "release_delay": 0.2,
                    },
                ],
                "name": "Foyer Keypad",
            }
        ],
        "port": 1234,
    }

    await hass.async_block_till_done()

    # Check the new entities were added
    assert len(hass.states.async_entity_ids(BINARY_SENSOR_DOMAIN)) == 3
    assert len(hass.states.async_entity_ids(BUTTON_DOMAIN)) == 4