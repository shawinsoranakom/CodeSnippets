async def test_options_flow_exclude_mode_advanced(hass: HomeAssistant) -> None:
    """Test config flow options in exclude mode with advanced options."""

    config_entry = _mock_config_entry_with_options_populated()
    config_entry.add_to_hass(hass)

    hass.states.async_set("climate.old", "off")
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "domains": ["fan", "vacuum", "climate", "humidifier"],
            "include_exclude_mode": "exclude",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "exclude"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entities": ["climate.old"]},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "advanced"

    with patch("homeassistant.components.homekit.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={},
        )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        "devices": [],
        "mode": "bridge",
        "filter": {
            "exclude_domains": [],
            "exclude_entities": ["climate.old"],
            "include_domains": ["fan", "vacuum", "climate", "humidifier"],
            "include_entities": [],
        },
    }