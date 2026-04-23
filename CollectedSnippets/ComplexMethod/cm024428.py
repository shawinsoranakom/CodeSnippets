async def test_full_flow_reconfigure(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_sma_client: AsyncMock,
) -> None:
    """Test the full flow of the config flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, unique_id="123456789")
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_RECONFIGURE,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "1.1.1.2"
    assert entry.data[CONF_SSL] is True
    assert entry.data[CONF_VERIFY_SSL] is False
    assert entry.data[CONF_GROUP] == "user"
    assert len(mock_setup_entry.mock_calls) == 1