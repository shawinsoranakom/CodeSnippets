async def test_user_flow_api_error(
    hass: HomeAssistant,
    mock_fishaudio_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    side_effect: Exception,
    error_base: str,
) -> None:
    """Test user flow with API errors during validation and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Simulate the error
    mock_fishaudio_client.account.get_credits.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "bad-key"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error_base}

    mock_setup_entry.assert_not_called()

    # Clear the error and retry successfully
    mock_fishaudio_client.account.get_credits.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "test-key"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Fish Audio"
    assert result["data"] == {CONF_API_KEY: "test-key", CONF_USER_ID: "test_user"}
    assert result["result"].unique_id == "test_user"

    mock_setup_entry.assert_called_once()