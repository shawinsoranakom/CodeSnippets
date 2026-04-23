async def test_user_step_error_recovery(
    hass: HomeAssistant,
    mock_redgtech_api: MagicMock,
    side_effect: Exception,
    expected_error: str,
) -> None:
    """Test that the flow can recover from errors and complete successfully."""
    user_input = {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}

    # Reset mock to start fresh
    mock_redgtech_api.login.reset_mock()
    mock_redgtech_api.login.return_value = None
    mock_redgtech_api.login.side_effect = None

    # First attempt fails with error
    mock_redgtech_api.login.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=user_input
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == expected_error
    # Verify login was called at least once for the first attempt
    assert mock_redgtech_api.login.call_count >= 1
    first_call_count = mock_redgtech_api.login.call_count

    # Second attempt succeeds - flow recovers
    mock_redgtech_api.login.side_effect = None
    mock_redgtech_api.login.return_value = FAKE_TOKEN
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_EMAIL
    assert result["data"] == user_input
    # Verify login was called again for the second attempt (recovery)
    assert mock_redgtech_api.login.call_count > first_call_count