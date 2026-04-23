async def test_options_add_remove_light_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_homeworks: MagicMock
) -> None:
    """Test options flow to add and remove a light."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.async_entity_ids("light") == unordered(["light.foyer_sconces"])

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "add_light"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_light"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDR: "[02:08:01:02]",
            CONF_NAME: "Foyer Downlights",
            CONF_RATE: 2.0,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "controller_id": "main_controller",
        "dimmers": [
            {"addr": "[02:08:01:01]", "name": "Foyer Sconces", "rate": 1.0},
            {"addr": "[02:08:01:02]", "name": "Foyer Downlights", "rate": 2.0},
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
            }
        ],
        "port": 1234,
    }

    await hass.async_block_till_done()

    # Check the entry was updated with the new entity
    assert hass.states.async_entity_ids("light") == unordered(
        ["light.foyer_sconces", "light.foyer_downlights"]
    )

    # Now remove the original light
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "remove_light"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "remove_light"
    assert result["data_schema"].schema["index"].options == {
        "0": "Foyer Sconces ([02:08:01:01])",
        "1": "Foyer Downlights ([02:08:01:02])",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_INDEX: ["0"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "controller_id": "main_controller",
        "dimmers": [
            {"addr": "[02:08:01:02]", "name": "Foyer Downlights", "rate": 2.0},
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
            }
        ],
        "port": 1234,
    }

    await hass.async_block_till_done()

    # Check the original entity was removed, with only the new entity left
    assert hass.states.async_entity_ids("light") == unordered(
        ["light.foyer_downlights"]
    )