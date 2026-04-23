async def test_full_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_nintendo_authenticator: AsyncMock,
    mock_nintendo_api: AsyncMock,
) -> None:
    """Test a full and successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result is not None
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "link" in result["description_placeholders"]
    assert result["description_placeholders"]["link"] == LOGIN_URL

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ACCOUNT_ID
    assert result["data"][CONF_SESSION_TOKEN] == API_TOKEN
    assert result["result"].unique_id == ACCOUNT_ID