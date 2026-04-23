async def test_user_flow_success(
    hass: HomeAssistant, mock_hass_splunk: AsyncMock
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: True,
            CONF_NAME: "Test Splunk",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "splunk.example.com:8088"
    assert result["data"] == {
        CONF_TOKEN: "test-token-123",
        CONF_HOST: "splunk.example.com",
        CONF_PORT: 8088,
        CONF_SSL: True,
        CONF_VERIFY_SSL: True,
        CONF_NAME: "Test Splunk",
    }

    # Verify that check was called twice (connectivity and token)
    assert mock_hass_splunk.check.call_count == 2