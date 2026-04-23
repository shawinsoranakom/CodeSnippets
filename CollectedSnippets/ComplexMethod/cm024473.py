async def test_reauth_2fa_flow(hass: HomeAssistant) -> None:
    """Test the reauth flow."""

    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: INCORRECT_PASSWORD,
            "tokens": {
                "AccessToken": "mock-access-token",
                "RefreshToken": "mock-refresh-token",
            },
        },
    )
    mock_config.add_to_hass(hass)

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        side_effect=hive_exceptions.HiveInvalidPassword(),
    ):
        result = await mock_config.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_password"}

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
                CONF_PASSWORD: UPDATED_PASSWORD,
            },
        )

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.sms_2fa",
            return_value={
                "ChallengeName": "SUCCESS",
                "AuthenticationResult": {
                    "RefreshToken": "mock-refresh-token",
                    "AccessToken": "mock-access-token",
                },
            },
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_CODE: MFA_CODE,
            },
        )
        await hass.async_block_till_done()

    assert mock_config.data.get("username") == USERNAME
    assert mock_config.data.get("password") == UPDATED_PASSWORD
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1