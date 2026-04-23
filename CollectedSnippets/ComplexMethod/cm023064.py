async def test_step_reauth_exceptions(
    hass: HomeAssistant,
    mock_powerfox_local_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test exceptions during re-authentication flow."""
    mock_powerfox_local_client.value.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key"},
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": error}

    # Recover from error
    mock_powerfox_local_client.value.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key"},
    )
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"

    assert mock_config_entry.data[CONF_API_KEY] == "new-api-key"