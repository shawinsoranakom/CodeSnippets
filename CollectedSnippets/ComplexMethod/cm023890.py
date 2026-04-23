async def test_config_flow(hass: HomeAssistant, qnap_connect: MagicMock) -> None:
    """Config flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    qnap_connect.get_system_stats.side_effect = ConnectTimeout("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    qnap_connect.get_system_stats.side_effect = TypeError("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

    qnap_connect.get_system_stats.side_effect = Exception("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unknown"}

    qnap_connect.get_system_stats.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test NAS name"
    assert result["data"] == ENTRY_DATA