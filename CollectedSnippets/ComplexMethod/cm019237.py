async def test_user_flow_exceptions(
    hass: HomeAssistant,
    mock_uhoo_client: AsyncMock,
    exception: Exception,
    error_type: str,
) -> None:
    """Test form when client raises various exceptions."""
    mock_uhoo_client.login.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "test-api-key"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error_type}

    mock_uhoo_client.login.assert_called_once()
    mock_uhoo_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "test-api-key"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY