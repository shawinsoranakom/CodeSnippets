async def test_reauthentication_fail(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_nintendo_authenticator: AsyncMock,
) -> None:
    """Test failed reauthentication."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    # Simulate invalid authentication by raising an exception
    mock_nintendo_authenticator.async_complete_login.side_effect = (
        InvalidSessionTokenException(status_code=401, message="Test")
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}

    # Now ensure that the flow can be recovered
    mock_nintendo_authenticator.async_complete_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"