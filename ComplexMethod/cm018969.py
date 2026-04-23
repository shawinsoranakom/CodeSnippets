async def test_user_flow_timeout(
    hass: HomeAssistant, mock_actron_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test OAuth2 flow when login task raises a non-CannotConnect exception."""

    # Override the default mock to raise a generic exception (not CannotConnect)
    async def raise_generic_error(device_code):
        raise RuntimeError("Unexpected error")

    mock_actron_api.poll_for_token = raise_generic_error

    # Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Task raises a non-CannotConnect exception, so it goes to timeout
    assert result["type"] is FlowResultType.SHOW_PROGRESS_DONE
    assert result["step_id"] == "timeout"

    # Continue to the timeout step
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should show the timeout form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "timeout"

    # Now fix the mock to allow successful token polling for recovery
    async def successful_poll_for_token(device_code):
        await asyncio.sleep(0.1)
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

    mock_actron_api.poll_for_token = successful_poll_for_token

    # User clicks retry button
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    # Should start progress again
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "user"
    assert result["progress_action"] == "wait_for_authorization"

    # Wait for the progress to complete
    await hass.async_block_till_done()

    # Continue the flow after progress is done
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should create entry on successful recovery
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"