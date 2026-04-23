async def test_async_step_reauth_confirm_failed_auth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    expected_error: str,
    mock_compit_api: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test reauth confirm step with invalid authentication then success after error is cleared."""
    mock_compit_api.side_effect = [exception, True]

    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["step_id"] == "reauth_confirm"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    # Test success after error is cleared
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: CONFIG_INPUT[CONF_EMAIL], CONF_PASSWORD: "correct-password"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_EMAIL: CONFIG_INPUT[CONF_EMAIL],
        CONF_PASSWORD: "correct-password",
    }
    assert len(mock_setup_entry.mock_calls) == 1