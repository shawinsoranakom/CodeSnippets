async def test_user_flow_oauth2_success(
    hass: HomeAssistant, mock_actron_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test successful OAuth2 device code flow."""
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

    # Continue the flow after progress is done - this should complete the entire flow
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Should create entry on successful token exchange
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"] == {
        CONF_API_TOKEN: "test_refresh_token",
    }
    assert result["result"].unique_id == "test_user_id"