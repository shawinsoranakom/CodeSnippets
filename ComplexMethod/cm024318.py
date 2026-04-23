async def test_error_scenarios(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_hanna_client: MagicMock,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test various error scenarios in the config flow."""
    mock_hanna_client.authenticate.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected_error}

    # Repatch to succeed and complete the flow
    mock_hanna_client.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"] == {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "test-password",
    }