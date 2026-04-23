async def test_user_flow_token_polling_error(
    hass: HomeAssistant, mock_actron_api, mock_setup_entry: AsyncMock
) -> None:
    """Test OAuth2 flow with error during token polling."""
    # Override the default mock to raise an error during token polling
    mock_actron_api.poll_for_token = AsyncMock(
        side_effect=ActronAirAuthError("Token polling error")
    )

    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Since the error occurs immediately, the task completes and we get progress_done
    assert result["type"] is FlowResultType.SHOW_PROGRESS_DONE
    assert result["step_id"] == "connection_error"

    # Continue to the connection_error step
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should show the connection error form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "connection_error"

    # Now fix the mock to allow successful token polling for recovery
    async def successful_poll_for_token(device_code):
        await asyncio.sleep(0.1)  # Small delay to allow progress state
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

    mock_actron_api.poll_for_token = successful_poll_for_token

    # User clicks retry button - this should restart the flow and succeed
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    # Should start progress again
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "user"
    assert result["progress_action"] == "wait_for_authorization"

    # Wait for the progress to complete
    await hass.async_block_till_done()

    # Continue the flow after progress is done - this should complete successfully
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should create entry on successful recovery
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"] == {
        CONF_API_TOKEN: "test_refresh_token",
    }
    assert result["result"].unique_id == "test_user_id"