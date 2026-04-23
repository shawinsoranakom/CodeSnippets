async def test_options_flow_include_mode_with_non_existant_entity(
    hass: HomeAssistant,
) -> None:
    """Test config flow options in include mode with a non-existent entity."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
        options={
            "filter": {
                "include_entities": ["climate.not_exist", "climate.front_gate"],
            },
        },
    )
    config_entry.add_to_hass(hass)
    hass.states.async_set("climate.front_gate", "off")
    hass.states.async_set("climate.new", "off")

    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "domains": ["fan", "vacuum", "climate"],
            "include_exclude_mode": "include",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "include"

    entities = result["data_schema"]({})["entities"]
    assert "climate.not_exist" not in entities

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": ["climate.new", "climate.front_gate"],
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["fan", "vacuum"],
            "include_entities": ["climate.new", "climate.front_gate"],
        },
    }
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(config_entry.entry_id)