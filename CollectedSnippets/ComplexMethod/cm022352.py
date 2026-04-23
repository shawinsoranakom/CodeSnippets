async def test_options_edit_light_no_lights_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_homeworks: MagicMock
) -> None:
    """Test options flow to edit a light."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.async_entity_ids("light") == unordered(["light.foyer_sconces"])

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "select_edit_light"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_edit_light"
    assert result["data_schema"].schema["index"].container == {
        "0": "Foyer Sconces ([02:08:01:01])"
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"index": "0"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "edit_light"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_RATE: 3.0}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "controller_id": "main_controller",
        "dimmers": [{"addr": "[02:08:01:01]", "name": "Foyer Sconces", "rate": 3.0}],
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

    # Check the entity was updated
    assert len(hass.states.async_entity_ids("light")) == 1