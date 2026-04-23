async def test_options_flow(hass: HomeAssistant) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options_1"

    section_marker, section_schema = list(result["data_schema"].schema.items())[0]
    assert section_marker == "section_1"
    section_schema_markers = list(section_schema.schema.schema)
    assert len(section_schema_markers) == 2
    assert section_schema_markers[0] == "bool"
    assert section_schema_markers[0].description is None
    assert section_schema_markers[1] == "int"
    assert section_schema_markers[1].description == {"suggested_value": 10}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"section_1": {"bool": True, "int": 15}},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"section_1": {"bool": True, "int": 15}}

    await hass.async_block_till_done()