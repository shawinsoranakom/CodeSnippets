async def test_reauth_flow(hass: HomeAssistant) -> None:
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
            "ChallengeName": "SUCCESS",
            "AuthenticationResult": {
                "RefreshToken": "mock-refresh-token",
                "AccessToken": "mock-access-token",
            },
        },
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: UPDATED_PASSWORD,
            },
        )
    await hass.async_block_till_done()

    assert mock_config.data.get("username") == USERNAME
    assert mock_config.data.get("password") == UPDATED_PASSWORD
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1