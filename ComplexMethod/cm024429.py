async def test_full_flow_reconfigure_exceptions(
    hass: HomeAssistant,
    mock_setup_entry: MockConfigEntry,
    mock_sma_client: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test we handle cannot connect error and recover from it."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, unique_id="123456789")
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_sma_client.new_session.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_RECONFIGURE,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_sma_client.new_session.side_effect = None
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