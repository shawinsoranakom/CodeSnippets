async def test_reauth(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test the start of the config flow."""
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    result = await config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["description_placeholders"] == {
        CONF_NAME: "Mock Title",
        CONF_USERNAME: "email@test.com",
    }
    assert result["errors"] == {}

    # Failed credentials
    with patch(
        "renault_api.renault_session.RenaultSession.login",
        side_effect=InvalidCredentialsException(403042, "invalid loginID or password"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: "any"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["description_placeholders"] == {
        CONF_NAME: "Mock Title",
        CONF_USERNAME: "email@test.com",
    }
    assert result2["errors"] == {"base": "invalid_credentials"}

    # Valid credentials
    with patch("renault_api.renault_session.RenaultSession.login"):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: "any"},
        )

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"

    assert config_entry.data[CONF_USERNAME] == "email@test.com"
    assert config_entry.data[CONF_PASSWORD] == "any"