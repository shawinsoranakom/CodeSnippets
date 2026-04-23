async def test_reconfigure_already_configured(
    hass: HomeAssistant, mock_nsapi: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test reconfiguring with an API key that's already used by another entry."""
    # Add first entry
    mock_config_entry.add_to_hass(hass)

    # Create and add second entry with different API key
    second_entry = MockConfigEntry(
        domain=DOMAIN,
        title="NS Integration 2",
        data={CONF_API_KEY: "another_api_key_456"},
        unique_id="second_entry",
    )
    second_entry.add_to_hass(hass)

    # Start reconfigure flow for the first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Try to reconfigure to use the API key from the second entry
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "another_api_key_456"}
    )

    # Should show error that it's already configured
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "already_configured"}

    # Verify the original entry was not changed
    assert mock_config_entry.data[CONF_API_KEY] == API_KEY

    # Now submit a valid unique API key to complete the flow
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "new_unique_key_789"}
    )

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_API_KEY] == "new_unique_key_789"