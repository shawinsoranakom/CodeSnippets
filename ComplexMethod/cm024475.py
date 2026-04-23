async def test_user_flow_2fa_no_internet_connection(hass: HomeAssistant) -> None:
    """Test user flow with no internet connection."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == CONF_CODE
    assert result2["errors"] == {}

    with patch(
        "homeassistant.components.hive.config_flow.Auth.sms_2fa",
        side_effect=hive_exceptions.HiveApiError(),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_CODE: MFA_CODE},
        )

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == CONF_CODE
    assert result3["errors"] == {"base": "no_internet_available"}