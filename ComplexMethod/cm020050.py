async def test_reauth(hass: HomeAssistant, config_entry_with_auth: ConfigEntry) -> None:
    """Test the start of the config flow."""
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    result = await config_entry_with_auth.start_reauth_flow(hass)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {}

    # Failed credentials
    with patch(
        "homeassistant.components.sfr_box.config_flow.SFRBox.authenticate",
        side_effect=SFRBoxAuthenticationError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "invalid",
            },
        )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": "invalid_auth"}

    # Valid credentials
    with patch("homeassistant.components.sfr_box.config_flow.SFRBox.authenticate"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "admin",
                CONF_PASSWORD: "new_password",
            },
        )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"