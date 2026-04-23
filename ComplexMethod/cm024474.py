async def test_user_flow_2fa_send_new_code(hass: HomeAssistant) -> None:
    """Resend a 2FA code if it didn't arrive."""
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
            {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == CONF_CODE
    assert result2["errors"] == {}

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {CONF_CODE: MFA_RESEND_CODE}
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == CONF_CODE
    assert result3["errors"] == {}

    with patch(
        "homeassistant.components.hive.config_flow.Auth.sms_2fa",
        return_value={
            "ChallengeName": "SUCCESS",
            "AuthenticationResult": {
                "RefreshToken": "mock-refresh-token",
                "AccessToken": "mock-access-token",
            },
        },
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CODE: MFA_CODE,
            },
        )

    assert result4["type"] is FlowResultType.FORM
    assert result4["step_id"] == "configuration"
    assert result4["errors"] == {}

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
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result5 = await hass.config_entries.flow.async_configure(
            result4["flow_id"], {CONF_DEVICE_NAME: DEVICE_NAME}
        )
        await hass.async_block_till_done()

    assert result5["type"] is FlowResultType.CREATE_ENTRY
    assert result5["title"] == USERNAME
    assert result5["data"] == {
        CONF_USERNAME: USERNAME,
        CONF_PASSWORD: PASSWORD,
        "tokens": {
            "AuthenticationResult": {
                "AccessToken": "mock-access-token",
                "RefreshToken": "mock-refresh-token",
            },
            "ChallengeName": "SUCCESS",
        },
        "device_data": [
            "mock-device-group-key",
            "mock-device-key",
            "mock-device-password",
        ],
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1