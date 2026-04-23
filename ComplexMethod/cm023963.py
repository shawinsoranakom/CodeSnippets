async def test_options_flow(
    hass: HomeAssistant,
    mock_setup_entry: None,
    init_integration: MockConfigEntry,
) -> None:
    """Test updating options."""
    entry = init_integration

    assert entry.options[CONF_UPCOMING_DAYS] == DEFAULT_UPCOMING_DAYS
    assert entry.options[CONF_WANTED_MAX_ITEMS] == DEFAULT_WANTED_MAX_ITEMS

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_UPCOMING_DAYS: 2, CONF_WANTED_MAX_ITEMS: 100},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_UPCOMING_DAYS] == 2
    assert result["data"][CONF_WANTED_MAX_ITEMS] == 100