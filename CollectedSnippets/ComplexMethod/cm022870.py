async def test_config_flow_already_configured(hass: HomeAssistant) -> None:
    """Test user config flow with two equal entries."""
    r1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert r1["type"] is FlowResultType.FORM
    assert r1["step_id"] == SOURCE_USER
    assert "flow_id" in r1
    result1 = await hass.config_entries.flow.async_configure(
        r1["flow_id"],
        user_input={CONF_LOCATION: DEFAULT_LOCATION},
    )
    assert result1["type"] is FlowResultType.CREATE_ENTRY

    r2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert r2["type"] is FlowResultType.FORM
    assert r2["step_id"] == SOURCE_USER
    assert "flow_id" in r2
    result2 = await hass.config_entries.flow.async_configure(
        r2["flow_id"],
        user_input={CONF_LOCATION: DEFAULT_LOCATION},
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"