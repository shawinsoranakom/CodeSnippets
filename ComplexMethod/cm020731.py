async def test_options_flow(
    hass: HomeAssistant, config_entry, setup_config_entry
) -> None:
    """Test config flow options."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    def get_schema_marker(data_schema: vol.Schema, key: str) -> vol.Marker:
        for k in data_schema.schema:
            if k == key and isinstance(k, vol.Marker):
                return k
        return None

    # Original schema uses defaults for suggested values:
    assert get_schema_marker(result["data_schema"], CONF_FROM_WINDOW).description == {
        "suggested_value": 3.5
    }
    assert get_schema_marker(result["data_schema"], CONF_TO_WINDOW).description == {
        "suggested_value": 3.5
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_FROM_WINDOW: 3.5, CONF_TO_WINDOW: 2.0}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {CONF_FROM_WINDOW: 3.5, CONF_TO_WINDOW: 2.0}

    # Subsequent schema uses previous input for suggested values:
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert get_schema_marker(result["data_schema"], CONF_FROM_WINDOW).description == {
        "suggested_value": 3.5
    }
    assert get_schema_marker(result["data_schema"], CONF_TO_WINDOW).description == {
        "suggested_value": 2.0
    }