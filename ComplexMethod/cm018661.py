async def test_options_settings(
    hass: HomeAssistant, config_entry, setup_config_entry
) -> None:
    """Test setting settings via the options flow."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "settings"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "settings"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"show_on_map": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "sensor_indices": [TEST_SENSOR_INDEX1],
        "show_on_map": True,
    }

    assert config_entry.options["show_on_map"] is True