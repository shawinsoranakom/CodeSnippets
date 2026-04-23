async def test_user_cloud_login_auth_failed(hass: HomeAssistant) -> None:
    """Test the cloud login flow with authentication failure."""
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

    # Test authentication failure
    with patch(
        "homeassistant.components.switchbot.config_flow.fetch_cloud_devices",
        side_effect=SwitchbotAuthenticationError("Invalid credentials"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test@example.com",
                CONF_PASSWORD: "wrongpass",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud_login"
    assert result["errors"] == {"base": "auth_failed"}
    assert "Invalid credentials" in result["description_placeholders"]["error_detail"]