async def test_reauth_flow_wrong_account(
    hass: HomeAssistant, mock_actron_api: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test reauthentication flow with wrong account."""
    # Create an existing config entry
    mock_config_entry.add_to_hass(hass)

    # Mock the API to return a different user ID
    mock_actron_api.get_user_info = AsyncMock(
        return_value=ActronAirUserInfo(
            id="different_user_id", email="different@example.com"
        )
    )

    # Start the reauth flow
    result = await mock_config_entry.start_reauth_flow(hass)

    # Should show the reauth confirmation form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Submit the confirmation form
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    # Should start with a progress step
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "user"
    assert result["progress_action"] == "wait_for_authorization"

    # Wait for the progress to complete
    await hass.async_block_till_done()

    # Continue the flow after progress is done
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should abort because of wrong account
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_account"