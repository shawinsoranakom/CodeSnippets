async def test_user_flow_duplicate_account(
    hass: HomeAssistant, mock_actron_api: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test duplicate account handling - should abort when same account is already configured."""
    # Create an existing config entry for the same user account
    mock_config_entry.add_to_hass(hass)

    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Should start with a progress step
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "user"
    assert result["progress_action"] == "wait_for_authorization"
    assert result["description_placeholders"] is not None
    assert "user_code" in result["description_placeholders"]
    assert result["description_placeholders"]["user_code"] == "ABC123"

    # Wait for the progress to complete
    await hass.async_block_till_done()

    # Continue the flow after progress is done
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should abort because the account is already configured
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"