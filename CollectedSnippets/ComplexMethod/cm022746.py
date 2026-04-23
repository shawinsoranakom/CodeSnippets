async def test_options_flow_exclude_mode_basic(hass: HomeAssistant) -> None:
    """Test config flow options in exclude mode."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_hass(hass)

    hass.states.async_set("climate.old", "off")
    hass.states.async_set("climate.front_gate", "off")

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
            "include_exclude_mode": "exclude",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "exclude"
    entities = result["data_schema"]({})["entities"]
    assert entities == ["climate.front_gate"]

    # Inject garbage to ensure the options data
    # is being deep copied and we cannot mutate it in flight
    config_entry.options[CONF_FILTER][CONF_INCLUDE_DOMAINS].append("garbage")

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entities": ["climate.old"]},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["climate.old"],
            "include_domains": ["fan", "vacuum", "climate"],
            "include_entities": [],
        },
    }