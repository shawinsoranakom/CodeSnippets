async def test_invalid_auth(
    hass: HomeAssistant,
    mock_nintendo_authenticator: AsyncMock,
    mock_nintendo_api: AsyncMock,
) -> None:
    """Test handling of invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result is not None
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "link" in result["description_placeholders"]

    # Simulate invalid authentication by raising an exception
    mock_nintendo_authenticator.async_complete_login.side_effect = (
        InvalidSessionTokenException(status_code=401, message="Test")
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "invalid_token"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

    # Now ensure that the flow can be recovered
    mock_nintendo_authenticator.async_complete_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ACCOUNT_ID
    assert result["data"][CONF_SESSION_TOKEN] == API_TOKEN
    assert result["result"].unique_id == ACCOUNT_ID