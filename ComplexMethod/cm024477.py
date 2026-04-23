async def test_user_flow_2fa_unknown_error(hass: HomeAssistant) -> None:
    """Test 2fa flow when unknown error occurs."""
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

    with patch(
        "homeassistant.components.hive.config_flow.Auth.sms_2fa",
        return_value={"ChallengeName": "FAILED", "InvalidAuthenticationResult": {}},
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_CODE: MFA_CODE},
        )

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "configuration"
    assert result3["errors"] == {}

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.device_registration",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.get_device_data",
            return_value=[
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        ),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE_NAME: DEVICE_NAME},
        )
        await hass.async_block_till_done()

    assert result4["type"] is FlowResultType.FORM
    assert result4["step_id"] == "configuration"
    assert result4["errors"] == {"base": "unknown"}