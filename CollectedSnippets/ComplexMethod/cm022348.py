async def test_options_add_light_flow(
    hass: HomeAssistant,
    mock_empty_config_entry: MockConfigEntry,
    mock_homeworks: MagicMock,
) -> None:
    """Test options flow to add a light."""
    mock_empty_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_empty_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.async_entity_ids("light") == unordered([])

    result = await hass.config_entries.options.async_init(
        mock_empty_config_entry.entry_id
    )
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
            {"addr": "[02:08:01:02]", "name": "Foyer Downlights", "rate": 2.0},
        ],
        "host": "192.168.0.1",
        "keypads": [],
        "port": 1234,
    }

    await hass.async_block_till_done()

    # Check the entry was updated with the new entity
    assert hass.states.async_entity_ids("light") == unordered(
        ["light.foyer_downlights"]
    )