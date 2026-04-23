async def test_config_flow_default(hass: HomeAssistant) -> None:
    """Test user config flow with default fields."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER
    assert "flow_id" in result

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: DEFAULT_LOCATION},
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == DEFAULT_LOCATION
    assert result2["result"].unique_id == DEFAULT_LOCATION
    assert result2["data"][CONF_LOCATION] == DEFAULT_LOCATION