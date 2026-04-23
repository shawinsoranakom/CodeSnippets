async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_actron_api: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test successful reauthentication flow."""
    # Create an existing config entry
    mock_config_entry.add_to_hass(hass)
    existing_entry = mock_config_entry

    # Start the reauth flow
    result = await mock_config_entry.start_reauth_flow(hass)

    # Should show the reauth confirmation form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Submit the confirmation form to start the OAuth flow
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    # Should start with a progress step
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "user"
    assert result["progress_action"] == "wait_for_authorization"

    # Wait for the progress to complete
    await hass.async_block_till_done()

    # Continue the flow after progress is done
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should update the existing entry with new token
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert existing_entry.data[CONF_API_TOKEN] == "test_refresh_token"