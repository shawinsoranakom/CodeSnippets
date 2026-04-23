async def test_full_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the full flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: "apiieu.ezvizlife.com",
        },
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