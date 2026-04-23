async def test_step_user_errors(
    hass: HomeAssistant,
    mock_api_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test error cases for user step with recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    user_input = {CONF_API_KEY: "some_api_key"}

    mock_api_client.async_get_devices.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "valid_api_key"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected_error}

    mock_api_client.async_get_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY