async def test_user_custom_url_unknown_exception(
    hass: HomeAssistant, mock_ezviz_client: AsyncMock
) -> None:
    """Test the full flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_ezviz_client.login.side_effect = Exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: CONF_CUSTOMIZE,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_custom_url"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "test-user"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unknown"