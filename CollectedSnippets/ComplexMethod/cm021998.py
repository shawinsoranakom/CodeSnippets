async def test_reauth_with_mfa_challenge(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the full interactive MFA flow during reauth."""
    # 1. Set up the existing entry and trigger reauth
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    hass.config.components.add(DOMAIN)
    mock_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"

    # 2. Test failure before MFA challenge (InvalidAuth)
    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
        side_effect=InvalidAuth,
    ) as mock_login_fail_auth:
        result_invalid_auth = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "bad-password",
            },
        )
    mock_login_fail_auth.assert_awaited_once()
    assert result_invalid_auth["type"] is FlowResultType.FORM
    assert result_invalid_auth["step_id"] == "reauth_confirm"
    assert result_invalid_auth["errors"] == {"base": "invalid_auth"}

    # 3. Test failure before MFA challenge (CannotConnect)
    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
        side_effect=CannotConnect,
    ) as mock_login_fail_connect:
        result_cannot_connect = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "new-password",
            },
        )
    mock_login_fail_connect.assert_awaited_once()
    assert result_cannot_connect["type"] is FlowResultType.FORM
    assert result_cannot_connect["step_id"] == "reauth_confirm"
    assert result_cannot_connect["errors"] == {"base": "cannot_connect"}

    # 4. Trigger the MfaChallenge on the next attempt
    mock_mfa_handler = AsyncMock()
    mock_mfa_handler.async_get_mfa_options.return_value = {
        "Email": "fooxxx@mail.com",
        "Phone": "xxx-123",
    }
    mock_mfa_handler.async_submit_mfa_code.return_value = {
        "login_data_mock_key": "login_data_mock_value"
    }
    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
        side_effect=MfaChallenge(message="", handler=mock_mfa_handler),
    ) as mock_login_mfa:
        result_mfa_challenge = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "new-password",
            },
        )
        mock_login_mfa.assert_awaited_once()

    # 5. Handle the happy path for the MFA flow
    assert result_mfa_challenge["type"] is FlowResultType.FORM
    assert result_mfa_challenge["step_id"] == "mfa_options"
    mock_mfa_handler.async_get_mfa_options.assert_awaited_once()

    result_mfa_code = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_method": "Phone"}
    )
    mock_mfa_handler.async_select_mfa_option.assert_awaited_once_with("Phone")
    assert result_mfa_code["type"] is FlowResultType.FORM
    assert result_mfa_code["step_id"] == "mfa_code"

    result_final = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_code": "good-code"}
    )
    mock_mfa_handler.async_submit_mfa_code.assert_awaited_once_with("good-code")

    # 6. Verify the reauth completes successfully
    assert result_final["type"] is FlowResultType.ABORT
    assert result_final["reason"] == "reauth_successful"
    await hass.async_block_till_done()

    # Check that data was updated and the entry was reloaded
    assert mock_config_entry.data["password"] == "new-password"
    assert mock_config_entry.data["login_data"] == {
        "login_data_mock_key": "login_data_mock_value"
    }
    assert len(mock_unload_entry.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1