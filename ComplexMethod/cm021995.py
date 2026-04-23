async def test_form_with_mfa_challenge(
    recorder_mock: Recorder, hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test the full interactive MFA flow, including error recovery."""
    # 1. Start the flow and get to the credentials step
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"utility": "Pacific Gas and Electric Company (PG&E)"},
    )

    # 2. Trigger an MfaChallenge on login
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
    ) as mock_login:
        result_challenge = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )
        mock_login.assert_awaited_once()

    # 3. Handle the MFA options step, starting with a connection error
    assert result_challenge["type"] is FlowResultType.FORM
    assert result_challenge["step_id"] == "mfa_options"
    mock_mfa_handler.async_get_mfa_options.assert_awaited_once()

    # Test CannotConnect on selecting MFA method
    mock_mfa_handler.async_select_mfa_option.side_effect = CannotConnect
    result_mfa_connect_fail = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_method": "Email"}
    )
    mock_mfa_handler.async_select_mfa_option.assert_awaited_once_with("Email")
    assert result_mfa_connect_fail["type"] is FlowResultType.FORM
    assert result_mfa_connect_fail["step_id"] == "mfa_options"
    assert result_mfa_connect_fail["errors"] == {"base": "cannot_connect"}

    # Retry selecting MFA method successfully
    mock_mfa_handler.async_select_mfa_option.side_effect = None
    result_mfa_select_ok = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_method": "Email"}
    )
    assert mock_mfa_handler.async_select_mfa_option.call_count == 2
    assert result_mfa_select_ok["type"] is FlowResultType.FORM
    assert result_mfa_select_ok["step_id"] == "mfa_code"

    # 4. Handle the MFA code step, testing multiple failure scenarios
    # Test InvalidAuth on submitting code
    mock_mfa_handler.async_submit_mfa_code.side_effect = InvalidAuth
    result_mfa_invalid_code = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_code": "bad-code"}
    )
    mock_mfa_handler.async_submit_mfa_code.assert_awaited_once_with("bad-code")
    assert result_mfa_invalid_code["type"] is FlowResultType.FORM
    assert result_mfa_invalid_code["step_id"] == "mfa_code"
    assert result_mfa_invalid_code["errors"] == {"base": "invalid_mfa_code"}

    # Test CannotConnect on submitting code
    mock_mfa_handler.async_submit_mfa_code.side_effect = CannotConnect
    result_mfa_code_connect_fail = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_code": "good-code"}
    )
    assert mock_mfa_handler.async_submit_mfa_code.call_count == 2
    mock_mfa_handler.async_submit_mfa_code.assert_called_with("good-code")
    assert result_mfa_code_connect_fail["type"] is FlowResultType.FORM
    assert result_mfa_code_connect_fail["step_id"] == "mfa_code"
    assert result_mfa_code_connect_fail["errors"] == {"base": "cannot_connect"}

    # Retry submitting code successfully
    mock_mfa_handler.async_submit_mfa_code.side_effect = None
    result_final = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"mfa_code": "good-code"}
    )
    assert mock_mfa_handler.async_submit_mfa_code.call_count == 3
    mock_mfa_handler.async_submit_mfa_code.assert_called_with("good-code")

    # 5. Verify the flow completes and creates the entry
    assert result_final["type"] is FlowResultType.CREATE_ENTRY
    assert (
        result_final["title"]
        == "Pacific Gas and Electric Company (PG&E) (test-username)"
    )
    assert result_final["data"] == {
        "utility": "Pacific Gas and Electric Company (PG&E)",
        "username": "test-username",
        "password": "test-password",
        "login_data": {"login_data_mock_key": "login_data_mock_value"},
    }
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1