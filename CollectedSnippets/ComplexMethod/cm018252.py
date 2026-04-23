async def test_cannot_connect(
    hass: HomeAssistant,
    mock_nintendo_authenticator: AsyncMock,
    mock_nintendo_api: AsyncMock,
) -> None:
    """Test handling of connection errors during device discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result is not None
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "link" in result["description_placeholders"]

    mock_nintendo_authenticator.async_complete_login.side_effect = None

    mock_nintendo_api.async_get_account_devices.side_effect = HttpException(
        status_code=500, message="TEST"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    # Test we can recover from the error
    mock_nintendo_api.async_get_account_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ACCOUNT_ID
    assert result["data"][CONF_SESSION_TOKEN] == API_TOKEN
    assert result["result"].unique_id == ACCOUNT_ID