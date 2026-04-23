async def test_user_custom_url_errors(
    hass: HomeAssistant,
    mock_ezviz_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test the full flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_ezviz_client.login.side_effect = exception

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

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_custom_url"
    assert result["errors"] == {"base": error}

    mock_ezviz_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "test-user"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username"
    assert result["data"] == {
        CONF_SESSION_ID: "fake_token",
        CONF_RFSESSION_ID: "fake_rf_token",
        CONF_URL: "apiieu.ezvizlife.com",
        CONF_TYPE: ATTR_TYPE_CLOUD,
    }
    assert result["result"].unique_id == "test-username"

    assert len(mock_setup_entry.mock_calls) == 1