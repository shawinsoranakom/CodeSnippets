async def test_reconfigure_password_error_then_recovery(
    hass: HomeAssistant,
    mock_growatt_classic_api: MagicMock,
    mock_config_entry_classic: MockConfigEntry,
    login_side_effect: Callable[..., Any] | Exception,
    expected_error: str,
) -> None:
    """Test password reconfigure shows error then allows recovery."""
    mock_config_entry_classic.add_to_hass(hass)

    result = await mock_config_entry_classic.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_growatt_classic_api.login.side_effect = login_side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_PASSWORD
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": expected_error}

    # Recover with correct credentials
    mock_growatt_classic_api.login.side_effect = None
    mock_growatt_classic_api.login.return_value = GROWATT_LOGIN_RESPONSE
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_PASSWORD
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"