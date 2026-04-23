async def test_config_flow_failure_api_exceptions(
    hass: HomeAssistant,
    exception: Exception,
    error_base: str,
    mock_setup_entry: AsyncMock,
    mock_touchlinesl_client: AsyncMock,
) -> None:
    """Test for invalid credentials or API connection errors, and that the form can recover."""
    mock_touchlinesl_client.user_id.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_DATA
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_base}

    # "Fix" the problem, and try again.
    mock_touchlinesl_client.user_id.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_DATA
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username"
    assert result["data"] == CONFIG_DATA
    assert result["result"].unique_id == RESULT_UNIQUE_ID
    assert len(mock_setup_entry.mock_calls) == 1