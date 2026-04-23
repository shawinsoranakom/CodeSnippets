async def test_reauth(
    hass: HomeAssistant,
    mock_latest_rates_config_flow: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test we can reauthenticate the config entry."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    mock_latest_rates_config_flow.side_effect = OpenExchangeRatesAuthError()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_key": "invalid-test-api-key",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    mock_latest_rates_config_flow.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_key": "new-test-api-key",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert len(mock_setup_entry.mock_calls) == 1