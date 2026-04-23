async def test_options_flow(hass: HomeAssistant) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_1"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"bool": True, "constant": "Constant Value", "int": 15},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_2"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "bool": True,
        "constant": "Constant Value",
        "int": 15,
        "multi": ["default"],
        "select": "default",
        "string": "Default",
    }

    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()