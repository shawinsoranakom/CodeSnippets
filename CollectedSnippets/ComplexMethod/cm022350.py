async def test_options_add_remove_keypad_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_homeworks: MagicMock,
    keypad_address: str,
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

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDR: keypad_address,
            CONF_NAME: "Hall Keypad",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "controller_id": "main_controller",
        "dimmers": [
            {"addr": "[02:08:01:01]", "name": "Foyer Sconces", "rate": 1.0},
        ],
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
                ],
                "name": "Foyer Keypad",
            },
            {"addr": keypad_address, "buttons": [], "name": "Hall Keypad"},
        ],
        "port": 1234,
    }

    await hass.async_block_till_done()

    # Now remove the original keypad
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "remove_keypad"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "remove_keypad"
    assert result["data_schema"].schema["index"].options == {
        "0": "Foyer Keypad ([02:08:02:01])",
        "1": f"Hall Keypad ({keypad_address})",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_INDEX: ["0"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "controller_id": "main_controller",
        "dimmers": [
            {"addr": "[02:08:01:01]", "name": "Foyer Sconces", "rate": 1.0},
        ],
        "host": "192.168.0.1",
        "keypads": [{"addr": keypad_address, "buttons": [], "name": "Hall Keypad"}],
        "port": 1234,
    }
    await hass.async_block_till_done()