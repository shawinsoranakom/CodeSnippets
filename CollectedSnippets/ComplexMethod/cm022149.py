async def test_step_mfa(hass: HomeAssistant) -> None:
    """Test that the MFA step works."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.abode.config_flow.Abode",
        side_effect=AbodeAuthenticationException(MFA_CODE_REQUIRED),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "mfa"

    with patch(
        "homeassistant.components.abode.config_flow.Abode",
        side_effect=AbodeAuthenticationException(
            (HTTPStatus.BAD_REQUEST, "invalid mfa")
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"mfa_code": "123456"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "mfa"
    assert result["errors"] == {"base": "invalid_mfa_code"}

    with patch("homeassistant.components.abode.config_flow.Abode"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"mfa_code": "123456"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "user@email.com"
    assert result["data"] == {
        CONF_USERNAME: "user@email.com",
        CONF_PASSWORD: "password",
        CONF_POLLING: False,
    }