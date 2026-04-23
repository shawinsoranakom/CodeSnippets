async def test_step_reauth_exceptions(
    hass: HomeAssistant,
    mock_autarco_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test exceptions in reauth flow."""
    mock_autarco_client.get_account.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "new-password"},
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": error}

    # Recover from error
    mock_autarco_client.get_account.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "new-password"},
    )
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"

    assert len(hass.config_entries.async_entries()) == 1
    assert mock_config_entry.data[CONF_PASSWORD] == "new-password"