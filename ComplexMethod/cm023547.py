async def test_user_cloud_login_api_error(hass: HomeAssistant) -> None:
    """Test the cloud login flow with API error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "cloud_login"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud_login"

    # Test API connection error
    with patch(
        "homeassistant.components.switchbot.config_flow.fetch_cloud_devices",
        side_effect=SwitchbotAccountConnectionError("API is down"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "testpass",
            },
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "api_error"
    assert result["description_placeholders"] == {"error_detail": "API is down"}